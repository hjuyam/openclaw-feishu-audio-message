# openclaw-feishu-audio-message

MVP: **send Feishu native voice-bubble** (`msg_type: "audio"`) using **offline TTS (Piper)** + `ffmpeg` + Feishu OpenAPI.

This repo intentionally **does not** include any models, temp audio artifacts, or secrets.

## What it does

- Text → (Piper) WAV → (ffmpeg) OPUS → (Feishu upload) `file_key` → (Feishu send) `msg_type=audio`
- Includes a lightweight offline ASR wrapper (Sherpa-ONNX Paraformer) as a building block
- Built-in temp cleanup policy: success delete immediately; failure keep TTL then purge

## Prerequisites

- Python 3.10+
- `ffmpeg`
- `piper` CLI (or `pip install piper-tts`)
- Python deps:
  - `requests`
  - `sherpa-onnx` (optional, for ASR)

> On Debian/Ubuntu you may hit PEP 668 “externally-managed”. Use a venv, or `pip --break-system-packages` if you accept the risk.

## Setup

1) Create `.env` from `.env.example`

```bash
cp .env.example .env
# fill FEISHU_APP_ID / FEISHU_APP_SECRET
```

2) Download models (optional but recommended for MVP)

```bash
bash scripts/download_models.sh
```

3) Install python deps

```bash
pip install -r requirements.txt
```

## Send a voice bubble (msg_type=audio)

DM to a user:

```bash
source .env
python3 scripts/feishu_audio_send.py \
  --receive-id-type open_id \
  --receive-id ou_xxx \
  --text "测试一下语音条。"
```

Send to a group:

```bash
source .env
python3 scripts/feishu_audio_send.py \
  --receive-id-type chat_id \
  --receive-id oc_xxx \
  --text "大家好。"
```

## Temp cleanup policy

- Temp dir: `FEISHU_VOICE_TMP_DIR` (default `./tmp/feishu_voice_mvp`)
- Failure TTL: `FEISHU_VOICE_FAIL_TTL_SECONDS` (default 1800)
- On success, temp wav/opus files are deleted immediately (best-effort).

## Security

- Never commit `.env`, tokens, or OpenClaw config files.
- Never commit models (`models/`) or generated audio.
- See `.gitignore`.

## License

MIT
