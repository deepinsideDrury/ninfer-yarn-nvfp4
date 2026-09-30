# Speculative-decoding A/B harness (MTP vs DFlash2)

Reproduces the long-context A/B numbers in the
[main README](../../README.md) ("Speculative decoding past the native window").
Compares the two speculative backends against the *same* fixed prompts on one server
(one engine at a time, port 11434):

| file | purpose |
|---|---|
| `bench.py` | sends the fixed prompt set, scrapes the engine's `timings` (prefill/decode tok/s, draft proposed/accepted, wall time), writes `results/<engine>/<case>.json`, prints a comparison table (`report`) |
| `gen_long.py` | deterministically regenerates `prompts/p3_long.txt` (~420K tokens, fixed seed; recalibrate `TOKEN_TARGET` / `CHARS_PER_TOKEN` if your artifact tokenizes differently) |
| `ab_driver.sh` | full A/B: dflash2 → mtp, all three cases, final state mtp running |
| `ab_driver_p3.sh` | long-context-only re-run (both engines) |
| `serve/dflash2.sh`, `serve/mtp.sh` | example 500K deployments (override `MODEL`, `ROOT`, `BIN` env vars) |
| `prompts/p1_short.txt`, `prompts/p2_medium.txt` | fixed hand-written prompts; the long one is generated |

The drivers `pkill` any running `ninfer-serve` and restart per engine — **requires
downtime** and interrupts every live session on that model. Final state: mtp server
running (nohup, survives the terminal closing).

```bash
python3 gen_long.py            # once, to create the long prompt
bash ab_driver.sh              # full A/B (~20-40 min, mostly the two 420K prefills)
python3 bench.py report        # comparison table + needle answers
```

`results/` and the generated `p3_long*.txt` are gitignored; they are local artifacts.
