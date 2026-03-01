#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "[promptfoo] OPENAI_API_KEY not set. Skipping gate."
  exit 0
fi

if ! command -v promptfoo >/dev/null 2>&1; then
  npm i -g promptfoo
fi

echo "[promptfoo] running regression gate"
promptfoo eval -c evals/promptfooconfig.yaml
