# StoryGen — Children's Audiobook Generator

**StoryGen** automates the creation of children's audiobooks: give it a topic, and it writes a multi-chapter story, edits it for consistency, and compiles a polished MP3 with distinct character voices.

---

## Features

- **Story generation** — Outline, protagonists, moral themes, chapter structure, and full narrative text from a single prompt
- **Automated editing** — Iterative grooming loops fix plot holes, contradictions, and logical flaws
- **Multi-speaker TTS** — Characters get distinct voices; narrator handles narration
- **Audiobook compilation** — Chapters merged into a single MP3 with adjustable playback speed
- **Configurable** — Target length in minutes, speech speed, chapter count, audience type

---

## Setup

```bash
# 1. Clone
git clone https://github.com/andrejsstepanovs/storygen-py.git
cd storygen-py

# 2. Create and fill environment file
cp .env.example .env
# Edit .env with your API keys

# 3. Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Verify TTS voices are available
python -m storygen.main story voices
```

### Required API Keys

| Key | Where to get |
|---|---|
| `LLM_API_KEY` | Your OpenCode / LLM gateway provider |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) — for Gemini TTS |

---

## Usage

```bash
# Generate + synthesize a full audiobook
python -m storygen.main story create "A tiny frog who wanted to fly"

# Write story text only (no audio)
python -m storygen.main story write "A sleepy dragon in a quiet volcano"

# Synthesize audio from an existing story JSON
python -m storygen.main story voice tmp/final_groomed_A_tiny_frog.json

# List available TTS voices
python -m storygen.main story voices
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--chapters` | auto | Number of chapters (0 = auto) |
| `--length-in-min` | 8 | Target audio length in minutes |
| `--speech-speed` | 1.0 | Playback speed (1.0 = normal) |
| `--preread-loops` | 2 | Grooming iterations |
| `--model` | deepseek-v4-flash | LLM model name |
| `--voice` | Puck | Default TTS voice |
| `--debug` | off | Verbose logging |

---

## Architecture

```
storygen/
├── main.py      # CLI (Typer)
├── config.py    # Pydantic settings / env loading
├── models.py    # Story, Chapter, Protagonist Pydantic models
├── chains.py    # LLM orchestration: outline → write → groom
├── prompts.py   # Prompt templates and grooming logic
├── tts.py       # TTS engine: dialogue parsing, Gemini API, ffmpeg
└── utils.py     # Word budget math, emoji cleanup, file I/O
```

**Flow:** `CLI` → `chains.py` (LLM) → `models.py` (state) → `tts.py` (Gemini TTS + ffmpeg) → `mp3/*.mp3`

---

## Output

Stories are saved as JSON snapshots before and after grooming:

```
tmp/
├── A_tiny_frog.json              # Raw generated
└── final_groomed_A_tiny_frog.json # Post-editing

mp3/
└── A_tiny_frog.mp3                # Final audiobook
```

---

## Requirements

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) (for audio merging and speed adjustment)
- Gemini TTS API access
- LLM gateway (OpenCode or compatible)