# openclaw-feishu-audio-message

本项目用于在 OpenClaw 中**发送飞书原生语音条**（IM `msg_type: "audio"`），走一条**免费 / 本地优先**的闭环链路：

- 离线 TTS（Piper）→ WAV
- `ffmpeg` → OPUS
- 飞书 OpenAPI 上传 → `file_key`
- 飞书 OpenAPI 发送 → `msg_type=audio`

它是一个**可跑通的 MVP**，重点在于：

- **传输正确性**：必须以 `msg_type=audio` 发送，才能呈现为“语音条”，而不是“附件文件”。
- **跨平台交付**：Windows / macOS / Linux 都能用。
- **磁盘安全清理**：临时音频自动删除；对 inbound 缓存提供 TTL 清理。

English version: [`README.md`](./README.md)

## 最简安装（交给你的 OpenClaw）

复制以下内容，发给你的 OpenClaw：

> 根据我的操作系统实际情况，安装 https://github.com/hjuyam/openclaw-feishu-audio-message/ 这个 skill（或仓库）。包括必要的依赖（Python/ffmpeg/Piper 等），优先使用 uv；Piper 优先二进制并说明如何配置 PIPER_BIN；不要让我粘贴任何 secret（我会自己填写 FEISHU_APP_ID/FEISHU_APP_SECRET）。

---

## 方案原则（Principles）

1) **本地优先 / 免费优先**
- 核心链路不依赖付费 API。
- Piper / Sherpa-ONNX 在本地运行。

2) **飞书原生体验**
- 发送语音必须是 `msg_type: "audio"` 才会显示为原生语音条。

3) **三层架构（建议的长期演进）**
- **L1 编排层（OpenClaw Skill）**：决定何时 STT/TTS、策略、错误处理
- **L2 渠道能力层（Feishu tool/plugin）**：上传 OPUS、发送 `msg_type=audio`
- **L3 语音引擎层（本地进程 / MCP / Docker）**：STT/TTS 推理、模型管理

当前仓库更像是 L2/L3 的 MVP，并提供 CLI，方便你后续封装成 OpenClaw Skill。

4) **安全与可控的存储清理**
- 不提交 secrets / 模型 / 生成的音频产物。
- 发送侧临时 WAV/OPUS 成功即删。
- inbound 音频缓存不立即删（便于排障），但支持 TTL 清理。

---

## 功能清单（What you get）

- ✅ 文本 → Piper(WAV) → ffmpeg(OPUS) → 上传 → 发送（`msg_type=audio`）
- ✅ 跨平台模型下载（Python 脚本）
- ✅ doctor 自检（含 Windows/mac/Linux 安装提示）
- ✅ 临时目录清理策略（成功即删；失败保留 TTL 再清理）
- ✅ inbound 音频缓存 TTL 清理（默认保留 24 小时）
- 🧩 离线 ASR（Sherpa-ONNX Paraformer）wrapper（作为后续“收语音→转写”的构件）

---

## 目录结构（Repository layout）

- `scripts/cli.py`：统一入口（跨平台）
- `scripts/doctor.py`：环境自检 + 安装提示
- `scripts/download_models.py`：跨平台模型下载
- `scripts/feishu_audio_send.py`：飞书上传+发送实现（`msg_type=audio`）
- `scripts/piper_tts.py`：Piper 调用封装（支持 `PIPER_BIN`）
- `scripts/sherpa_offline_recognize.py`：Sherpa 离线转写封装
- `scripts/cleanup.py`：临时文件清理工具
- `scripts/cleanup_inbound.py`：inbound 媒体缓存 TTL 清理

---

## 快速开始（跨平台）

### 0) 安装依赖

需要：
- Python 3.10+
- `ffmpeg`
- Piper（推荐用二进制）

**强烈推荐：使用 `uv` 做依赖隔离（Win/mac/Linux 一致）**

- 安装 uv： https://docs.astral.sh/uv/getting-started/installation/

创建 venv 并安装 Python 依赖：

```bash
uv venv
uv pip install -r requirements.txt
```

> 兜底方案：`python -m venv .venv`，然后用对应平台路径安装：
> - Windows：`.venv\Scripts\pip install -r requirements.txt`
> - macOS/Linux：`.venv/bin/pip install -r requirements.txt`

### 1) doctor 自检

```bash
python scripts/cli.py doctor
# 可选：验证 FEISHU_APP_ID/SECRET 是否可用（不会打印 secret）
python scripts/doctor.py --check-feishu
```

### 2) 配置环境变量

从 `.env.example` 复制一份：

```bash
cp .env.example .env
```

填写：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`

可选：
- `PIPER_BIN`（如果你的 piper 不在 PATH，就写绝对路径）

### 3) 下载模型（推荐）

```bash
python scripts/cli.py download-models
```

### 4) 发送测试语音条

**自动目标**（更适合后续 OpenClaw Skill 注入当前会话目标）：

```bash
export FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id
export FEISHU_DEFAULT_RECEIVE_ID=ou_xxx
python scripts/cli.py send-test
```

或者显式指定：

```bash
python scripts/cli.py send \
  --receive-id-type open_id \
  --receive-id ou_xxx \
  --text "你好，这是飞书原生语音条。"
```

---

## 体验优化：语音前置 0.8 秒静音

部分客户端会“吃掉”语音条开头，尤其是短语音。这里在编码前会给 WAV 前拼一段静音。

- 默认：`FEISHU_VOICE_LEADING_SILENCE_MS=800`
- 设为 `0` 可关闭。

---

## 清理策略（Disk cleanup）

### 临时音频（WAV/OPUS）

- 临时目录：`FEISHU_VOICE_TMP_DIR`（默认 `./tmp/feishu_voice_mvp`）
- 失败保留：`FEISHU_VOICE_FAIL_TTL_SECONDS`（默认 `1800` = 30 分钟）
- 成功发送后：临时 WAV/OPUS 会尽力立即删除。

### OpenClaw inbound 媒体缓存（音频）

OpenClaw 会把你发来的附件/音频落在 `~/.openclaw/media/inbound` 这样的目录下。
本项目**不建议立即删除**（便于排障/复盘），但提供 TTL 清理。

Dry-run：

```bash
python scripts/cli.py cleanup-inbound --dry-run
```

删除超过 24 小时的音频文件：

```bash
python scripts/cli.py cleanup-inbound
```

配置项：
- `OPENCLAW_INBOUND_DIR`（默认 `/root/.openclaw/media/inbound`）
- `OPENCLAW_INBOUND_AUDIO_TTL_HOURS`（默认 `24`）

---

## Windows / macOS / Linux 差异点说明

### Python 环境

- 推荐 `uv`：跨平台体验最一致。
- 用 `venv` 时路径不同：
  - Windows：`.venv\Scripts\python`、`.venv\Scripts\pip`
  - macOS/Linux：`.venv/bin/python`、`.venv/bin/pip`

### ffmpeg 安装

- Windows：
  - `winget install Gyan.FFmpeg`（或 `choco install ffmpeg`）
- macOS：
  - `brew install ffmpeg`
- Linux：
  - Debian/Ubuntu：`sudo apt-get install ffmpeg`
  - 其他发行版用自己的包管理器

### Piper 安装

推荐：使用 Piper release 的二进制
- https://github.com/rhasspy/piper/releases

如果用二进制安装，请配置 `PIPER_BIN=/absolute/path/to/piper`。

兜底：`pip install piper-tts`（某些 Linux 发行版可能遇到 PEP668 / 包管理差异）。

---

## 安全说明（Security）

- 不要提交 `.env`、token、OpenClaw 配置、模型文件、生成的音频。
- 详见 `.gitignore`。

---

## License

MIT
