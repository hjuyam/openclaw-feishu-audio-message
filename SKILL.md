# feishu-audio-message (MVP)

**Goal:** send **Feishu native voice bubble** (IM `msg_type: "audio"`) from OpenClaw using **offline TTS (Piper)** + `ffmpeg` + Feishu OpenAPI.

This skill/repo focuses on the **transport correctness** (upload OPUS → `file_key` → `msg_type=audio`) and a **cross-platform delivery** experience.

## What you get

- ✅ Text → Piper (WAV) → ffmpeg (OPUS) → Feishu upload → Feishu send (`msg_type=audio`)
- ✅ Cross-platform model download (Python script)
- ✅ Preflight doctor checks (ffmpeg/piper/env)
- ✅ Temp cleanup policy (success delete immediately; failure keep TTL then purge)
- 🧩 Offline ASR wrapper (Sherpa-ONNX) included as a building block

## Requirements (cross-platform)

- Python 3.10+
- `ffmpeg`
- Piper **binary preferred** (or `pip install piper-tts`)
- Feishu app credentials in env: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`

## Quick start (recommended)

1) Preflight:

```bash
python scripts/cli.py doctor
```

2) Download models (optional but recommended):

```bash
python scripts/cli.py download-models
```

3) Create `.env` from `.env.example` and fill secrets.

4) Send a test voice bubble:

- Option A (explicit):

```bash
python scripts/cli.py send --receive-id-type open_id --receive-id ou_xxx --text "测试一下语音条。"
```

- Option B (auto target): set env and omit args:

```bash
# default target for send-test
export FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id
export FEISHU_DEFAULT_RECEIVE_ID=ou_xxx
python scripts/cli.py send-test
```

## Notes

- This repo **does not** commit any models, temp audio artifacts, or secrets.
- Prefer `uv` for dependency isolation across Win/macOS/Linux.

## Files

- `scripts/cli.py` – unified entrypoint
- `scripts/doctor.py` – environment checks + install hints
- `scripts/download_models.py` – cross-platform model downloader
- `scripts/feishu_audio_send.py` – actual Feishu audio send implementation
