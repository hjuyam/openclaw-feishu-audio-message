#!/usr/bin/env python3
"""Doctor: preflight checks + platform-specific install hints.

This is designed for Win/macOS/Linux.

Checks:
- Python version
- ffmpeg presence
- piper binary presence (prefer configurable path)
- Required env vars presence (without printing secrets)
- Optional: Feishu token fetch test

Usage:
  python scripts/doctor.py
  python scripts/doctor.py --check-feishu

Env:
  PIPER_BIN: path to piper executable (optional)
  FEISHU_APP_ID / FEISHU_APP_SECRET (required for Feishu check)
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from typing import Tuple

import requests


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run_version(cmd: list[str]) -> Tuple[bool, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return True, out.strip().splitlines()[0][:200]
    except Exception as e:
        return False, str(e)


def hint_ffmpeg() -> str:
    sysname = platform.system().lower()
    if sysname == "darwin":
        return "Install ffmpeg: brew install ffmpeg"
    if sysname == "windows":
        return "Install ffmpeg: winget install Gyan.FFmpeg (or choco install ffmpeg)"
    return "Install ffmpeg: sudo apt-get install ffmpeg (or your distro package manager)"


def hint_uv() -> str:
    sysname = platform.system().lower()
    if sysname == "windows":
        return "Install uv: https://docs.astral.sh/uv/getting-started/installation/ (PowerShell installer)"
    return "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"


def hint_piper() -> str:
    return (
        "Install Piper (binary preferred):\n"
        "- https://github.com/rhasspy/piper/releases\n"
        "Then set PIPER_BIN to the piper executable path, or ensure `piper` is in PATH.\n"
        "(Fallback: pip install piper-tts)"
    )


def feishu_base() -> str:
    return os.getenv("FEISHU_DOMAIN", "https://open.feishu.cn").rstrip("/")


def check_feishu_token() -> Tuple[bool, str]:
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        return False, "FEISHU_APP_ID / FEISHU_APP_SECRET not set"

    url = f"{feishu_base()}/open-apis/auth/v3/tenant_access_token/internal"
    try:
        r = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=20)
        j = r.json()
    except Exception as e:
        return False, f"request failed: {e}"

    if j.get("code") != 0:
        return False, f"token API returned code={j.get('code')} msg={j.get('msg')}"
    return True, "token fetch ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-feishu", action="store_true", help="Call Feishu token API to validate credentials")
    args = ap.parse_args()

    ok_all = True

    print("== System")
    print(f"platform: {platform.platform()}")
    print(f"python: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        ok_all = False
        print("[FAIL] Python >= 3.10 required")

    print("\n== Dependency: uv (recommended)")
    uv = which("uv")
    if uv:
        ok, ver = run_version([uv, "--version"])
        print(f"[OK] uv: {ver}")
    else:
        print("[WARN] uv not found")
        print("       " + hint_uv())

    print("\n== Dependency: ffmpeg")
    ff = which("ffmpeg")
    if ff:
        ok, ver = run_version([ff, "-version"])
        print(f"[OK] ffmpeg: {ver}")
    else:
        ok_all = False
        print("[FAIL] ffmpeg not found")
        print("       " + hint_ffmpeg())

    print("\n== Dependency: piper")
    piper_bin = os.getenv("PIPER_BIN") or which("piper")
    if piper_bin:
        ok, ver = run_version([piper_bin, "--help"])
        if ok:
            print(f"[OK] piper found: {piper_bin}")
        else:
            ok_all = False
            print(f"[FAIL] piper exists but not runnable: {piper_bin}")
            print(f"       {ver}")
            print(hint_piper())
    else:
        ok_all = False
        print("[FAIL] piper not found")
        print(hint_piper())

    print("\n== Env")
    def present(name: str) -> str:
        return "set" if os.getenv(name) else "missing"

    print(f"FEISHU_APP_ID: {present('FEISHU_APP_ID')}")
    print(f"FEISHU_APP_SECRET: {present('FEISHU_APP_SECRET')}")

    if args.check_feishu:
        print("\n== Feishu token check")
        ok, msg = check_feishu_token()
        if ok:
            print(f"[OK] {msg}")
        else:
            ok_all = False
            print(f"[FAIL] {msg}")

    print("\n== Result")
    if ok_all:
        print("OK")
        return 0
    else:
        print("NOT_OK")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
