# StoryGen — Children's Audiobook Generator

**StoryGen** automates the creation of children's audiobooks: give it a topic, and it writes a multi-chapter story, edits it for consistency, and compiles a polished MP3 with distinct character voices.

---

## Features

- **Story generation** — Outline, protagonists, moral themes, chapter structure, and full narrative text from a single prompt
- **Automated editing** — Iterative grooming loops fix plot holes, contradictions, and logical flaws
- **Multi-speaker TTS** — Characters get distinct voices; narrator handles narration
- **Audiobook compilation** — Chapters merged into a single MP3 with adjustable playback speed
- **Configurable** — Target length in minutes, speech speed, chapter count, audience type
- **Multi-provider LLM** — Works with OpenAI, Anthropic (via proxy), OpenRouter, OpenCode, and any OpenAI-compatible endpoint

---

## Setup

```bash
# 1. Clone
git clone https://github.com/andrejsstepanovs/storygen-py.git
cd storygen-py

# 2. Create and fill environment file
cp .env.example .env
# Edit .env with your API keys (see LLM Providers section below)

# 3. Install dependencies
uv sync

# 4. Verify it works
uv run storygen --help
```

---

## LLM Providers

StoryGen uses LangChain's `ChatOpenAI` with an OpenAI-compatible interface, so it works with any provider that speaks the OpenAI API format. Edit `.env` to switch.

### OpenAI (official)

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
MODEL_NAME=gpt-4o-mini
```

### OpenRouter (recommended — OpenAI + Anthropic + Gemini + many others)

Sign up at [openrouter.ai/keys](https://openrouter.ai/keys). Supports Anthropic Claude models natively.

```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
# Anthropic
MODEL_NAME=anthropic/claude-sonnet-4-20250514
# OpenAI
MODEL_NAME=openai/gpt-4o-mini
# Google
MODEL_NAME=google/gemini-2.0-flash-exp
```

### OpenCode Zen (current default)

```env
LLM_BASE_URL=https://opencode.ai/zen/go/v1
LLM_API_KEY=sk-...
MODEL_NAME=deepseek-v4-flash
```

### Other OpenAI-compatible providers

Any provider using the standard `/v1/chat/completions` endpoint works — Portkey, Cloudflare Workers AI, self-hosted vLLM, etc. Just set `LLM_BASE_URL` and `LLM_API_KEY` accordingly.

---

## Usage

```bash
# Generate + synthesize a full audiobook
uv run storygen story create "A tiny frog who wanted to fly"

# Write story text only (no audio)
uv run storygen story write "A sleepy dragon in a quiet volcano"

# Synthesize audio from an existing story JSON
uv run storygen story voice tmp/final_groomed_A_tiny_frog.json

# List available TTS voices
uv run storygen story voices

# Full help (all commands and options)
uv run storygen --help
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
- Gemini TTS API access (`GOOGLE_API_KEY` from [Google AI Studio](https://aistudio.google.com/app/apikey))
- LLM provider with OpenAI-compatible API