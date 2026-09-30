#!/bin/bash
# A/B: dflash2 vs mtp on identical prompts (p1 short / p2 medium / p3 ~420k needle).
# REQUIRES DOWNTIME: the model backend (including any live agent sessions) is
# interrupted while servers restart. Final state: mtp server running.
# Override the engine commands with DFLASH2_SERVE / MTP_SERVE env vars.
#   bash ab_driver.sh
set -u
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"
mkdir -p results
DFLASH2_SERVE=${DFLASH2_SERVE:-$HERE/serve/dflash2.sh}
MTP_SERVE=${MTP_SERVE:-$HERE/serve/mtp.sh}

wait_ready() {
  local i
  for i in $(seq 1 90); do
    if curl -sf -m 5 http://127.0.0.1:11434/v1/models >/dev/null 2>&1; then
      return 0
    fi
    sleep 5
  done
  echo "FATAL: server did not become ready" >&2
  return 1
}

start_engine() {
  local tag=$1 script=$2
  pkill -f ninfer-serve || true
  sleep 10  # let GPU memory be released
  nohup bash "$script" > "results/${tag}.server.log" 2>&1 &
  echo "started ${tag} via ${script} (nohup pid $!)"
  wait_ready || exit 1
  sleep 5  # settle before first request
}

echo "== [1/2] dflash2 =="
start_engine dflash2 "$DFLASH2_SERVE"
python3 bench.py run dflash2 || echo "dflash2 run had failures (see results/dflash2.server.log)"

echo "== [2/2] mtp =="
start_engine mtp "$MTP_SERVE"
python3 bench.py run mtp || echo "mtp run had failures (see results/mtp.server.log)"

python3 bench.py report
echo
echo "done. mtp server is running now."
