#!/usr/bin/env python3
"""A/B bench driver for ninfer-serve (dflash2 vs mtp), same host:port.

Usage:
  python3 bench.py run  <engine-tag> [base-url] [only-case]
  python3 bench.py report

Results are written to results/<engine-tag>/<case>.json (full answer + timings)
and printed as one JSON row per case for the log.
"""
import glob
import json
import os
import sys
import time
import urllib.request

BASE_DEFAULT = os.environ.get("NINFER_BASE", "http://127.0.0.1:11434")
MODEL = os.environ.get("NINFER_MODEL", "qwen3.8-27b")
HERE = os.path.dirname(os.path.abspath(__file__))

# (case_id, prompt file, max_tokens, note)
CASES = [
    ("p1_short", "prompts/p1_short.txt", 256, "short chat, thinking mode"),
    ("p2_medium", "prompts/p2_medium.txt", 512, "code bug fix, thinking mode"),
    ("p3_long", "prompts/p3_long.txt", 768, "~420k-token YaRN needle (beyond native 262144), thinking mode"),
]


def post(base, payload, timeout=1800):
    req = urllib.request.Request(
        base + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def run_case(base, tag, case_id, text, max_tokens):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": text}],
        "max_tokens": max_tokens,
        "stream": False,
    }
    t0 = time.time()
    d = post(base, payload)
    wall = time.time() - t0
    m = d["choices"][0]["message"]
    t = d.get("timings", {}) or {}
    draft_n = t.get("draft_n") or 0
    accepted = t.get("draft_n_accepted") or 0
    row = {
        "engine": tag,
        "case": case_id,
        "prompt_n": t.get("prompt_n"),
        "prompt_ms": t.get("prompt_ms"),
        "prefill_tok_s": t.get("prompt_per_second"),
        "generated_n": t.get("predicted_n"),
        "gen_tok_s": t.get("predicted_per_second"),
        "draft_n": draft_n or None,
        "draft_accepted": accepted or None,
        "accept_rate": round(accepted / draft_n, 4) if draft_n else None,
        "wall_s": round(wall, 3),
        "finish_reason": d["choices"][0].get("finish_reason"),
    }
    outdir = os.path.join(HERE, "results", tag)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, case_id + ".json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "row": row,
                "content": m.get("content", ""),
                "reasoning": m.get("reasoning_content", ""),
            },
            f,
            ensure_ascii=False,
            indent=1,
        )
    print(json.dumps(row, ensure_ascii=False), flush=True)
    return row


def cmd_run():
    tag = sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else BASE_DEFAULT
    only = sys.argv[4] if len(sys.argv) > 4 else None
    # Warmup: first request pays graph qualification / path setup costs.
    post(base, {"model": MODEL, "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1}, timeout=300)
    print("warmup done", flush=True)
    for case_id, rel, mt, note in CASES:
        if only and case_id != only:
            continue
        with open(os.path.join(HERE, rel), encoding="utf-8") as f:
            text = f.read()
        print(f"== {case_id} ({note}, {len(text)} chars) ==", flush=True)
        run_case(base, tag, case_id, text, mt)


def cmd_report():
    rows = []
    for p in sorted(glob.glob(os.path.join(HERE, "results", "*", "*.json"))):
        with open(p, encoding="utf-8") as f:
            rows.append(json.load(f)["row"])
    if not rows:
        print("no results yet")
        return
    hdr = (f"{'engine':8} {'case':10} {'prompt_n':>9} {'prefill t/s':>12} "
           f"{'gen t/s':>8} {'draft_n':>8} {'accepted':>8} {'acc %':>7} {'wall s':>8}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        acc = "" if r["accept_rate"] is None else f"{r['accept_rate'] * 100:.1f}"
        print(
            f"{r['engine']:8} {r['case']:10} {str(r['prompt_n']):>9} "
            f"{str(round(r['prefill_tok_s'] or 0)):>12} {str(round(r['gen_tok_s'] or 0)):>8} "
            f"{str(r['draft_n'] or '-'):>8} {str(r['draft_accepted'] or '-'):>8} "
            f"{acc:>7} {r['wall_s']:>8}"
        )
    for tag in ("dflash2", "mtp"):
        p = os.path.join(HERE, "results", tag, "p3_long.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            print(f"\nneedle answer [{tag}]: {d['content'][:200]!r}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        cmd_run()
    elif len(sys.argv) >= 2 and sys.argv[1] == "report":
        cmd_report()
    else:
        print(__doc__)
        sys.exit(1)
