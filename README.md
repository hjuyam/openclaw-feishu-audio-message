# openclaw-feishu-audio-message

Send **Feishu native voice bubbles** (IM `msg_type: "audio"`) from OpenClaw using a **free / local-first** pipeline:

- Offline TTS (Piper) → WAV
- `ffmpeg` → OPUS
- Feishu OpenAPI upload → `file_key`
- Feishu OpenAPI send → `msg_type=audio`

This repository is a **practical MVP** that emphasizes:

- **Transport correctness** (send as *voice bubble*, not as a file attachment)
- **Cross-platform delivery** (Win/macOS/Linux)
- **Safe cleanup** (temp artifacts deleted automatically; inbound cache TTL cleanup)

中文说明见：[`README.zh-CN.md`](./README.zh-CN.md)

## Ultra-minimal install (ask your OpenClaw)

Copy the text below and send it to your OpenClaw:

> Based on my OS (Windows/macOS/Linux), help me install this skill/repo: https://github.com/hjuyam/openclaw-feishu-audio-message/ . Include all required dependencies (Python/ffmpeg/Piper, etc.). Prefer uv; prefer Piper binary and explain how to set PIPER_BIN; do not ask me to paste any secrets (I will fill FEISHU_APP_ID/FEISHU_APP_SECRET myself).

---

## Principles

1) **Local-first, free-first**
- No paid APIs are required for the core path.
- Piper and Sherpa-ONNX run locally.

2) **Feishu-native UX**
- Outbound voice must be sent as `msg_type: "audio"` to appear as a native voice bubble.

3) **Separation of concerns (recommended 3-layer architecture)**
- **L1 Orchestration (OpenClaw Skill)**: decide when to STT/TTS, apply policies, error handling
- **L2 Channel capability (Feishu tool/plugin)**: upload OPUS, send `msg_type=audio`
- **L3 Voice engine (local process / MCP / Docker)**: STT/TTS inference, model management

This repo is currently an MVP that covers a large part of L2/L3, and provides a CLI that can be wrapped by an OpenClaw Skill.

4) **Safety & clean disk**
- Do not commit secrets/models/audio artifacts.
- Delete temp WAV/OPUS on success.
- Keep inbound cache for debugging, then cleanup by TTL.

---

## What you get

- ✅ Text → Piper (WAV) → ffmpeg (OPUS) → Feishu upload → Feishu send (`msg_type=audio`)
- ✅ Cross-platform model download (Python)
- ✅ Doctor preflight checks with platform hints
- ✅ Temp cleanup policy (success delete immediately; failure keep TTL then purge)
- ✅ Inbound audio cache cleanup by TTL (default: 24 hours)
- 🧩 Offline ASR wrapper (Sherpa-ONNX Paraformer) included as a building block

---

## Repository layout

- `scripts/cli.py` – unified cross-platform CLI entrypoint
- `scripts/doctor.py` – environment checks + install hints
- `scripts/download_models.py` – cross-platform model downloader
- `scripts/feishu_audio_send.py` – Feishu upload+send implementation (`msg_type=audio`)
- `scripts/piper_tts.py` – Piper TTS wrapper (supports `PIPER_BIN`)
- `scripts/sherpa_offline_recognize.py` – Sherpa offline ASR wrapper
- `scripts/cleanup.py` – temp cleanup helpers
- `scripts/cleanup_inbound.py` – inbound media cache cleanup (TTL)

---

## Quick start (cross-platform)

### 0) Install dependencies

You need:
- Python 3.10+
- `ffmpeg`
- Piper (binary preferred)

**Recommended: `uv` for dependency isolation**

- Install uv: https://docs.astral.sh/uv/getting-started/installation/

Create venv and install python deps:

```bash
uv venv
uv pip install -r requirements.txt
```

> Fallback: `python -m venv .venv` then install with `.venv/bin/pip` (macOS/Linux) or `.venv\Scripts\pip` (Windows).

### 1) Preflight check

```bash
python scripts/cli.py doctor
# optional: verify FEISHU_APP_ID/SECRET works
python scripts/doctor.py --check-feishu
```

### 2) Configure env

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Fill:
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`

Optional:
- `PIPER_BIN` (path to piper executable if it is not in PATH)

### 3) Download models (optional but recommended)

```bash
python scripts/cli.py download-models
```

### 4) Send a test voice bubble

**Auto target** (recommended when you wrap this into an OpenClaw Skill):

```bash
export FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id
export FEISHU_DEFAULT_RECEIVE_ID=ou_xxx
python scripts/cli.py send-test
```

Or explicit send:

```bash
python scripts/cli.py send \
  --receive-id-type open_id \
  --receive-id ou_xxx \
  --text "Hello from Feishu audio bubble"
```

---

## Playback UX tweak: leading silence

Some clients clip the very beginning of short voice bubbles. We prepend a short silence before encoding.

Note: The default voice model in this repo is a small one, so the speech may sound a bit stiff. If your machine has more CPU/RAM, consider switching to a higher-quality Piper voice/model.

- Default: `FEISHU_VOICE_LEADING_SILENCE_MS=800`
- Set to `0` to disable.

---

## Cleanup policies

### Temp artifacts (WAV/OPUS)

- Temp dir: `FEISHU_VOICE_TMP_DIR` (default `./tmp/feishu_voice_mvp`)
- Failure TTL: `FEISHU_VOICE_FAIL_TTL_SECONDS` (default `1800` = 30 minutes)
- On success, temp WAV/OPUS are deleted immediately (best-effort).

### OpenClaw inbound media cache (audio)

OpenClaw stores inbound attachments under a media cache directory (commonly `~/.openclaw/media/inbound`).
This project does **not** delete inbound files immediately (useful for debugging), but provides TTL cleanup.

Dry-run:

```bash
python scripts/cli.py cleanup-inbound --dry-run
```

Delete audio files older than 24 hours:

```bash
python scripts/cli.py cleanup-inbound
```

Configuration:
- `OPENCLAW_INBOUND_DIR` (default `/root/.openclaw/media/inbound`)
- `OPENCLAW_INBOUND_AUDIO_TTL_HOURS` (default `24`)

---

## Platform notes (Windows / macOS / Linux)

### Python environment

- Use **uv** whenever possible for the most consistent cross-platform experience.
- If you must use `venv`, paths differ:
  - Windows: `.venv\Scripts\python` and `.venv\Scripts\pip`
  - macOS/Linux: `.venv/bin/python` and `.venv/bin/pip`

### ffmpeg installation

- Windows:
  - `winget install Gyan.FFmpeg` (or `choco install ffmpeg`)
- macOS:
  - `brew install ffmpeg`
- Linux:
  - `sudo apt-get install ffmpeg` (Debian/Ubuntu)
  - or your distro package manager

### Piper installation

Preferred: Piper standalone binary
- https://github.com/rhasspy/piper/releases

If installed as a standalone binary, set `PIPER_BIN=/absolute/path/to/piper`.

Fallback: `pip install piper-tts` (may hit packaging/PEP668 differences on some Linux distros).

---

## Security

- Never commit `.env`, tokens, OpenClaw configs, models, or generated audio.
- See `.gitignore`.

---

## License

MIT
