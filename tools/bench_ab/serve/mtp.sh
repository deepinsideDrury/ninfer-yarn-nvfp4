#!/bin/bash
# Example 500K deployment with MTP speculation (RTX 5090, 32 GB).
# The artifact must carry an mtp component.
#   MODEL - .ninfer artifact path
#   ROOT  - repo root containing build/ (defaults to this file's git toplevel)
#   BIN   - serve binary (defaults to $ROOT/build/apps/ninfer-serve)
set -u
MODEL=${MODEL:-/home/drury/qwen3_8_27b_quasar_nvfp4.ninfer}
ROOT=${ROOT:-$(git -C "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel 2>/dev/null || echo "")}
BIN=${BIN:-$ROOT/build/apps/ninfer-serve}
exec "$BIN" "$MODEL" \
  --host 0.0.0.0 --port 11434 \
  --max-concurrency 2 \
  --rope-yarn-factor 4 --rope-original-max-position 262144 \
  --max-context 500000 \
  --kv-capacity 500000 \
  --default-max-tokens 65536 \
  --kv-dtype nvfp4 \
  --spec mtp --draft-tokens 3 --lm-head-draft \
  --device-state-slots 2 \
  --host-state-slots 8 \
  --host-kv-mib 10240 \
  --preserve-thinking \
  --vision
