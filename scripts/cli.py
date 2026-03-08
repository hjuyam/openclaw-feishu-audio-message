#!/usr/bin/env python3
"""Unified CLI entrypoint (cross-platform).

Commands:
  doctor                Preflight checks
  download-models       Download ASR/TTS models
  cleanup-inbound       Cleanup OpenClaw inbound audio cache by TTL
  send                  Send a Feishu native voice bubble (msg_type=audio)
  send-test             Send a canned test voice bubble to default target

Env shortcuts:
  FEISHU_DEFAULT_RECEIVE_ID_TYPE (default: open_id)
  FEISHU_DEFAULT_RECEIVE_ID

  PIPER_BIN / PIPER_VOICE / PIPER_VOICE_CONFIG
  FEISHU_APP_ID / FEISHU_APP_SECRET

Examples:
  python scripts/cli.py doctor
  python scripts/cli.py download-models
  python scripts/cli.py send --receive-id-type open_id --receive-id ou_xxx --text "hi"
  FEISHU_DEFAULT_RECEIVE_ID=ou_xxx python scripts/cli.py send-test
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_py(script: str, argv: list[str]) -> int:
    cmd = [sys.executable, str(ROOT / script), *argv]
    return subprocess.call(cmd)


def cmd_doctor(_args: argparse.Namespace) -> int:
    return run_py("doctor.py", [])


def cmd_download_models(args: argparse.Namespace) -> int:
    argv: list[str] = []
    if args.models_dir:
        argv += ["--models-dir", args.models_dir]
    return run_py("download_models.py", argv)


def cmd_send(args: argparse.Namespace) -> int:
    argv: list[str] = [
        "--receive-id-type",
        args.receive_id_type,
        "--receive-id",
        args.receive_id,
    ]

    if args.text:
        argv += ["--text", args.text]
    else:
        argv += ["--wav", args.wav]

    return run_py("feishu_audio_send.py", argv)


def cmd_cleanup_inbound(args: argparse.Namespace) -> int:
    argv: list[str] = []
    if args.dir:
        argv += ["--dir", args.dir]
    if args.ttl_hours is not None:
        argv += ["--ttl-hours", str(args.ttl_hours)]
    if args.dry_run:
        argv += ["--dry-run"]
    return run_py("cleanup_inbound.py", argv)


def cmd_send_test(args: argparse.Namespace) -> int:
    rid_type = os.getenv("FEISHU_DEFAULT_RECEIVE_ID_TYPE", "open_id")
    rid = os.getenv("FEISHU_DEFAULT_RECEIVE_ID")
    if not rid:
        print(
            "ERROR: FEISHU_DEFAULT_RECEIVE_ID is not set. "
            "Set FEISHU_DEFAULT_RECEIVE_ID / FEISHU_DEFAULT_RECEIVE_ID_TYPE or use `send --receive-id ...`",
            file=sys.stderr,
        )
        return 2

    argv = [
        "--receive-id-type",
        rid_type,
        "--receive-id",
        rid,
        "--text",
        args.text or "测试一下语音条。",
    ]
    return run_py("feishu_audio_send.py", argv)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor")
    p.set_defaults(fn=cmd_doctor)

    p = sub.add_parser("download-models")
    p.add_argument("--models-dir", help="Where to store downloaded models (default: ./models)")
    p.set_defaults(fn=cmd_download_models)

    p = sub.add_parser("cleanup-inbound")
    p.add_argument("--dir", help="Inbound dir (default: /root/.openclaw/media/inbound or OPENCLAW_INBOUND_DIR)")
    p.add_argument("--ttl-hours", type=float, help="TTL hours (default 24 or OPENCLAW_INBOUND_AUDIO_TTL_HOURS)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_cleanup_inbound)

    p = sub.add_parser("send")
    p.add_argument("--receive-id-type", required=True, choices=["open_id", "chat_id", "user_id", "union_id"])
    p.add_argument("--receive-id", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--wav")
    p.set_defaults(fn=cmd_send)

    p = sub.add_parser("send-test")
    p.add_argument("--text", help="Optional override test text")
    p.set_defaults(fn=cmd_send_test)

    args = ap.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
