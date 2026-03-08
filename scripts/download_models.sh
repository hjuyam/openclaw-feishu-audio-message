#!/usr/bin/env bash
set -euo pipefail

# Download lightweight models for MVP.
# - Sherpa-ONNX paraformer zh-small (offline ASR)
# - Piper zh_CN huayan x_low (offline TTS)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"

mkdir -p "$MODELS_DIR/sherpa" "$MODELS_DIR/piper"

echo "==> Download sherpa-onnx paraformer zh-small (int8)"
cd "$MODELS_DIR/sherpa"
if [[ ! -d sherpa-onnx-paraformer-zh-small-2024-03-09 ]]; then
  wget -q https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2
  tar xf sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2
  rm sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2
fi

echo "==> Download piper voice zh_CN huayan x_low"
cd "$MODELS_DIR/piper"
if [[ ! -f zh_CN-huayan-x_low.onnx ]]; then
  wget -q -O zh_CN-huayan-x_low.onnx https://huggingface.co/csukuangfj/vits-piper-zh_CN-huayan-x_low/resolve/main/zh_CN-huayan-x_low.onnx
fi
if [[ ! -f zh_CN-huayan-x_low.onnx.json ]]; then
  wget -q -O zh_CN-huayan-x_low.onnx.json https://huggingface.co/csukuangfj/vits-piper-zh_CN-huayan-x_low/resolve/main/zh_CN-huayan-x_low.onnx.json
fi

echo "Done. Models saved under: $MODELS_DIR"
