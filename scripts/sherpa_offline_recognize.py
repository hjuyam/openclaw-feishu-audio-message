#!/usr/bin/env python3
"""Offline STT wrapper using sherpa-onnx (paraformer).

Usage:
  python3 scripts/sherpa_offline_recognize.py <wav_path>

Env:
  SHERPA_ONNX_MODEL_DIR: directory containing the paraformer model and tokens.txt

Output:
  Prints recognized text to stdout.

Notes:
- Input should be WAV. If not mono/16k/PCM16, we normalize with ffmpeg (temp file).
"""

from __future__ import annotations

import os
import subprocess
import sys
import wave
from array import array
from pathlib import Path

import sherpa_onnx

from cleanup import new_temp_path, purge_expired, safe_unlink


def build_recognizer(model_dir: Path) -> sherpa_onnx.OfflineRecognizer:
    model = None
    for cand in [
        model_dir / "model.int8.onnx",
        model_dir / "model.onnx",
        model_dir / "model.fp32.onnx",
    ]:
        if cand.exists():
            model = cand
            break
    if model is None:
        raise FileNotFoundError(f"No paraformer model found in {model_dir}")

    tokens = model_dir / "tokens.txt"
    if not tokens.exists():
        raise FileNotFoundError(f"tokens.txt not found in {model_dir}")

    return sherpa_onnx.OfflineRecognizer.from_paraformer(
        paraformer=str(model),
        tokens=str(tokens),
        num_threads=1,
        sample_rate=16000,
        feature_dim=80,
        decoding_method="greedy_search",
        debug=False,
        provider="cpu",
    )


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(__doc__.strip())
        return 0

    purge_expired()

    wav_path = Path(sys.argv[1]).expanduser().resolve()
    if not wav_path.exists():
        print(f"ERROR: file not found: {wav_path}", file=sys.stderr)
        return 2

    model_dir = os.getenv("SHERPA_ONNX_MODEL_DIR")
    if not model_dir:
        print("ERROR: SHERPA_ONNX_MODEL_DIR is not set", file=sys.stderr)
        return 2

    model_dir_path = Path(model_dir).expanduser().resolve()
    if not model_dir_path.exists():
        print(f"ERROR: model dir not found: {model_dir_path}", file=sys.stderr)
        return 2

    recognizer = build_recognizer(model_dir_path)
    stream = recognizer.create_stream()

    tmp = None
    path_to_read = wav_path

    with wave.open(str(wav_path), "rb") as wf:
        nch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sr = wf.getframerate()

    if nch != 1 or sampwidth != 2 or sr != 16000:
        tmp = new_temp_path("stt-norm", ".wav")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(tmp),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        path_to_read = tmp

    try:
        with wave.open(str(path_to_read), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            samples_i16 = array("h")
            samples_i16.frombytes(frames)

        samples = [s / 32768.0 for s in samples_i16]
        stream.accept_waveform(16000, samples)

        recognizer.decode_stream(stream)
        result = stream.result
        print((result.text or "").strip())
        return 0
    finally:
        if tmp is not None:
            safe_unlink(tmp)


if __name__ == "__main__":
    raise SystemExit(main())
