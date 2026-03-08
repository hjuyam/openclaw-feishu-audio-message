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
- Piper binary (preferred) from releases, or `pip install piper-tts`
- (Optional) Sherpa-ONNX for offline ASR

## Quick start (cross-platform)

We provide a unified CLI entrypoint:

```bash
python scripts/cli.py doctor
python scripts/cli.py download-models
python scripts/cli.py cleanup-inbound --dry-run
python scripts/cli.py send-test
```

### 0) Preflight check

```bash
python scripts/doctor.py
# optional: verify FEISHU_APP_ID/SECRET works
python scripts/doctor.py --check-feishu
```

### 1) Setup env

Create `.env` from `.env.example`:

```bash
cp .env.example .env
# fill FEISHU_APP_ID / FEISHU_APP_SECRET
```

If you installed Piper as a standalone binary, set:

```bash
# example
PIPER_BIN=/absolute/path/to/piper
```

### 2) Download models (cross-platform)

```bash
python scripts/download_models.py
```

(For macOS/Linux users, `scripts/download_models.sh` is also provided.)

### 3) Install python deps (recommended: uv)

Using **uv** (recommended for Win/macOS/Linux):

```bash
uv venv
uv pip install -r requirements.txt
```

Fallback:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\pip install -r requirements.txt
# macOS/Linux: .venv/bin/pip install -r requirements.txt
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

## Playback UX tweak (leading silence)

Some clients may clip the very beginning of short audio bubbles. This project can prepend a small silence padding before encoding.

- Default: `FEISHU_VOICE_LEADING_SILENCE_MS=500`
- Set to `0` to disable.

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
