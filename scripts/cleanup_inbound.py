#!/usr/bin/env python3
"""Cleanup OpenClaw inbound media audio cache by TTL.

Why:
- OpenClaw stores inbound attachments under a media cache directory.
- We don't want to delete immediately (debug/retry), but we also don't want disk to grow unbounded.

Default policy (per user choice):
- Keep inbound audio files for 24 hours, then delete.

Safety:
- Only deletes known audio extensions.
- Only operates inside the configured inbound dir.

Usage:
  python scripts/cleanup_inbound.py
  python scripts/cleanup_inbound.py --dir /path/to/inbound --ttl-hours 24
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

AUDIO_EXTS = {".ogg", ".wav", ".opus", ".mp3", ".m4a", ".aac"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dir",
        default=os.getenv("OPENCLAW_INBOUND_DIR", "/root/.openclaw/media/inbound"),
        help="OpenClaw inbound media directory",
    )
    ap.add_argument(
        "--ttl-hours",
        type=float,
        default=float(os.getenv("OPENCLAW_INBOUND_AUDIO_TTL_HOURS", "24")),
        help="Delete files older than this many hours (default 24)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    inbound = Path(args.dir).expanduser().resolve()
    if not inbound.exists() or not inbound.is_dir():
        print(f"Inbound dir not found: {inbound}")
        return 2

    ttl_sec = args.ttl_hours * 3600
    now = time.time()

    deleted = 0
    scanned = 0

    for p in inbound.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in AUDIO_EXTS:
            continue
        scanned += 1
        try:
            age = now - p.stat().st_mtime
        except Exception:
            continue
        if age <= ttl_sec:
            continue

        if args.dry_run:
            print(f"DRY delete: {p.name}")
        else:
            try:
                p.unlink(missing_ok=True)
                deleted += 1
                print(f"Deleted: {p.name}")
            except Exception as e:
                print(f"Failed delete {p.name}: {e}")

    print(f"Scanned audio files: {scanned}")
    print(f"Deleted: {deleted}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
