#!/bin/bash
# Re-run ONLY the p3 long-context case on both engines.
# Same downtime contract as ab_driver.sh; final state: mtp server running.
#   bash ab_driver_p3.sh
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
  sleep 10
  nohup bash "$script" > "results/${tag}.server.log" 2>&1 &
  echo "started ${tag} via ${script} (nohup pid $!)"
  wait_ready || exit 1
  sleep 5
}

echo "== [1/2] dflash2 p3_long =="
start_engine dflash2 "$DFLASH2_SERVE"
python3 bench.py run dflash2 http://127.0.0.1:11434 p3_long \
  || echo "dflash2 p3 failed (see results/dflash2.server.log)"

echo "== [2/2] mtp p3_long =="
start_engine mtp "$MTP_SERVE"
python3 bench.py run mtp http://127.0.0.1:11434 p3_long \
  || echo "mtp p3 failed (see results/mtp.server.log)"

python3 bench.py report
echo
echo "done. mtp server is running now."
