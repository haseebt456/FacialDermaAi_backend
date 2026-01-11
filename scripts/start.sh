#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=5000}"
: "${PYTORCH_MODEL_PATH:=/app/best_model.pth}"

# Optional: download model at startup if a URL is provided
if [[ -n "${PYTORCH_MODEL_URL:-}" ]]; then
  echo "[start] Downloading model from ${PYTORCH_MODEL_URL} to ${PYTORCH_MODEL_PATH}"
  mkdir -p "$(dirname "${PYTORCH_MODEL_PATH}")"
  if ! curl -fL "${PYTORCH_MODEL_URL}" -o "${PYTORCH_MODEL_PATH}"; then
    echo "[start] WARNING: Failed to download model from ${PYTORCH_MODEL_URL}" >&2
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
