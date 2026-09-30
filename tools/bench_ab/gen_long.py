#!/usr/bin/env python3
"""Generate the deterministic ~380k-token long-context prompt (p3_long.txt).

English prose estimates at ~3.8 chars/token for the Qwen tokenizer. The first
bench run reports the real prompt_n; if it is outside (350k, 480k), adjust
TOKEN_TARGET and re-run this script (the prompt must stay identical across
engines, so re-run only before any bench has happened).
"""
import os
import random
import sys

# Calibrated from the first run: 1,444,294 chars -> 206,731 tokens (~6.99 chars/token).
TOKEN_TARGET = 420_000
CHARS_PER_TOKEN = 7.0
SEED = 20260930
NEEDLE = "SECRET_MARKER_7QX: The purple otter's unlock code is 424242."
QUESTION = ("The document above is generated filler. Somewhere near the end it "
            "contains one sentence that begins with 'SECRET_MARKER_7QX'. Quote "
            "that sentence exactly, character for character, on a single line. "
            "Do not add any other commentary.")

VOCAB = (
    "engineering systems runtime memory context window attention position "
    "encoding rotation frequency scaling extension inference decode generate "
    "token sequence model weights gradient precision quantization format cache "
    "kernel launch thread warp block tensor matrix projection layer norm "
    "residual connection softmax sampling decoding speculation draft verify "
    "accept reject proposal candidate rank selector projection convolution "
    "window sliding causal mask padding alignment chunk stream batch request "
    "response latency throughput bandwidth throughput allocation reservation "
    "arena slab page group index offset cursor pointer reference handle "
    "binding scope lifetime ownership move copy construct destroy finalizer "
    "observer callback scheduler executor queue priority deadline timeout "
    "retry backoff budget quota limit capacity reservation compaction "
    "eviction checkpoint snapshot restore migrate replicate shard partition "
    "balance workload throughput efficiency utilization pressure throttle "
    "saturation degradation fallback bypass shortcut optimize profile measure "
    "benchmark calibration regression drift variance stddev percentile "
    "latency tail jitter queueing arrival service completion pipeline stage "
    "phase barrier synchronization lock mutex atomic spin yield resume "
    "interrupt signal handler dispatcher router multiplexer demultiplexer "
    "adapter bridge proxy decorator factory builder template strategy "
    "state machine transition invariant constraint validation assertion "
    "exception fault error warning notice diagnostic telemetry metric gauge "
    "histogram counter sample trace span event log line buffer ring deque "
    "stack heap graph node edge path tree branch leaf root parent child "
    "sibling ancestor descendant prefix suffix substring pattern match "
    "search lookup index hash map set list array vector tuple record struct "
    "field property attribute descriptor registry catalog inventory census "
    "survey probe sensor gauge meter scale ruler measure dimension extent "
    "boundary margin border edge fringe periphery core center middle third "
    "quarter half double triple single multiple several many few several "
).split()


def main():
    rng = random.Random(SEED)
    target_chars = int(TOKEN_TARGET * CHARS_PER_TOKEN)
    parts = []
    produced = 0
    # Build sentences of 8-16 words, paragraphs of 5-9 sentences.
    while produced < target_chars:
        para = []
        for _ in range(rng.randint(5, 9)):
            n_words = rng.randint(8, 16)
            words = [rng.choice(VOCAB) for _ in range(n_words)]
            words[0] = words[0].capitalize()
            sent = " ".join(words) + "."
            para.append(sent)
        text = " ".join(para) + "\n\n"
        parts.append(text)
        produced += len(text)
    body = "".join(parts)[:target_chars]
    # Insert the needle in the final paragraph, then the question.
    body = body.rstrip() + "\n\n" + NEEDLE + "\n\n" + QUESTION + "\n"
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "prompts", "p3_long.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"wrote {out}: {len(body)} chars, ~{len(body) // CHARS_PER_TOKEN} "
          f"estimated tokens")
    if len(body) > 480_000 * CHARS_PER_TOKEN:
        print("WARNING: estimated tokens exceed max_context 500000; lower "
              "TOKEN_TARGET", file=sys.stderr)


if __name__ == "__main__":
    main()
