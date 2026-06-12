import os
import re
import base64
import requests
import subprocess
from pathlib import Path
from storygen.config import settings
from storygen.models import Story
from storygen.utils import vprint

DIALOGUE_PATTERN = re.compile(
    r'(\w+)\s+(?:said|whispered|shouted|yelled|cried|asked|replied|answered|insisted|exclaimed|muttered|groaned|gasped|laughed|called|added|continued|began|told|ordered|screamed|begged|complained|sobbed|demanded|explained|promised|warned|agreed|admitted|announced|boasted|confessed|declared|hissed|moaned|mumbled|pleaded|roared|snapped|suggested|urged)\s+"([^"]*)"',
    re.IGNORECASE
)

def build_speaker_voices(story: Story) -> dict[str, str]:
    mapping = {}
    for p in story.protagonists:
        voice = settings.voice_male if p.gender.lower() in ["male", "boy"] else settings.voice_female
        mapping[p.name.lower()] = voice
    if story.villain and story.villain.name:
        villain_name = story.villain.name.split()[0].strip(',.;:!?"\'()')
        mapping[villain_name.lower()] = settings.voice_male 
    return mapping

def convert_narrative_to_script(text: str, speaker_mapping: dict[str, str]) -> tuple[str, list[dict]]:
    lines = []
    used_speakers = {}
    last_end = 0

    for match in DIALOGUE_PATTERN.finditer(text):
        speaker = match.group(1)
        dialogue = match.group(2)
        
        narration = text[last_end:match.start()].strip()
        if narration:
            lines.append(f"Narrator: {narration}")
            
        speaker_lower = speaker.lower()
        if speaker_lower in speaker_mapping:
            used_speakers[speaker] = speaker_mapping[speaker_lower]
            lines.append(f"{speaker}: {dialogue}")
        else:
            lines.append(f"Narrator: {speaker} said \"{dialogue}\"")
            
        last_end = match.end()

    narration_after = text[last_end:].strip()
    if narration_after:
        lines.append(f"Narrator: {narration_after}")

    if used_speakers:
        used_speakers["Narrator"] = settings.voice

    speaker_configs = [{"speaker": k, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": v}}} for k, v in used_speakers.items()]
    return "\n".join(lines), speaker_configs

def generate_tts(text: str, story: Story, output_path: str):
    speaker_mapping = build_speaker_voices(story)
    script_text, speaker_configs = convert_narrative_to_script(text, speaker_mapping)

    url = f"{settings.tts_base_url}/{settings.tts_model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.google_api_key}

    speech_config = {}
    if speaker_configs:
        speech_config["multiSpeakerVoiceConfig"] = {"speakerVoiceConfigs": speaker_configs}
    else:
        speech_config["voiceConfig"] = {"prebuiltVoiceConfig": {"voiceName": settings.voice}}

    payload = {
        "contents": [{"parts": [{"text": script_text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": speech_config
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    pcm_data = None
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                pcm_data = base64.b64decode(part["inlineData"]["data"])
                break
    
    if not pcm_data:
        raise ValueError("No audio data returned from Gemini TTS")

    pcm_file = f"{output_path}.pcm"
    with open(pcm_file, "wb") as f:
        f.write(pcm_data)

    subprocess.run([
        "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", 
        "-i", pcm_file, "-c:a", "libmp3lame", "-q:a", "0", output_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(pcm_file)

def compile_audiobook(story: Story, filename: str):
    os.makedirs(settings.target_dir, exist_ok=True)
    full_text = story.build_content()
    chapters = re.split(r'\n(?:...\n)?\s*Chapter (?:[1-9]\d*)\.', full_text)
    
    mp3_files = []
    for i, ch_text in enumerate(chapters):
        vprint(f"[bold yellow]Generating audio for chapter {i}...[/bold yellow]")
        if not ch_text.strip():
            continue
        out_path = Path(settings.tmp_dir) / f"{i}_{filename}.mp3"
        generate_tts(ch_text.strip(), story, str(out_path))
        mp3_files.append(str(out_path))
        
    final_path = Path(settings.target_dir) / f"{filename}.mp3"
    
    concat_list = Path(settings.tmp_dir) / "concat.txt"
    with open(concat_list, "w") as f:
        for mp3 in mp3_files:
            f.write(f"file '{Path(mp3).absolute()}'\n")

    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list)
    ]
    
    if settings.speech_speed != 1.0:
        ffmpeg_cmd.extend(["-filter:a", f"atempo={settings.speech_speed}", "-c:a", "libmp3lame", "-q:a", "0"])
    else:
        ffmpeg_cmd.extend(["-c", "copy"])
        
    ffmpeg_cmd.append(str(final_path))
    
    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os.remove(concat_list)
    for mp3 in mp3_files:
        os.remove(mp3)
