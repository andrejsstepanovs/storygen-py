import os
import re
import json
from pathlib import Path
from pydantic import BaseModel
from storygen.config import settings
from rich import print as rprint

def vprint(*args, **kwargs):
    if settings.verbose:
        rprint(*args, **kwargs)

def get_chapter_count_and_length() -> tuple[int, int, str]:
    minutes = settings.length_in_min
    
    # Base reading speed (e.g. 132 wpm) scaled by the TTS speech speed
    effective_wpm = int(settings.readspeed * settings.speech_speed)
    total_words = minutes * effective_wpm
    
    # Target ~2.5 minutes of audio per chapter if not explicitly set
    chapter_count = settings.chapters or max(1, round(minutes / 2.5))
    
    max_chapter_words = total_words // chapter_count
    
    length_text = f"Target length: {minutes} minutes (speed {settings.speech_speed}x). Total words: ~{total_words}. Chapter count: {chapter_count}. Max chapter words: {max_chapter_words} words."
    return chapter_count, max_chapter_words, length_text

def get_chapter_word_counts(chapter_count: int, max_words: int) -> dict[int, int]:
    counts = {}
    if chapter_count == 1:
        counts[1] = max_words
        return counts
        
    for i in range(1, chapter_count + 1):
        if i == 1:
            counts[i] = int(max_words * 0.8)
        elif i == chapter_count:
            counts[i] = int(max_words * 0.6)
        else:
            counts[i] = max_words
    return counts

def sanitize_filename(filename: str) -> str:
    filename = filename.replace('"', '').replace('.', '_').replace(' ', '_')
    filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '', filename)
    return filename[:150]

def save_json(obj: BaseModel, prefix: str, dir_path: str = settings.tmp_dir) -> str:
    os.makedirs(dir_path, exist_ok=True)
    filename = f"{sanitize_filename(prefix)}.json"
    filepath = Path(dir_path) / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(obj.model_dump_json(indent=2))
    return str(filepath)

def load_json(filepath: str, model: type[BaseModel]) -> BaseModel:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return model.model_validate(data)

def remove_emojis(text: str) -> str:
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]', '', text)
    text = re.sub(r'[\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF]', '', text)
    text = re.sub(r'[\u200B\u200C\u200D\uFEFF]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
