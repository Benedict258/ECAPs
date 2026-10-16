"""Real smoke test: `python -m ecaps.smoke [--url http://127.0.0.1:8080]`.
Needs a running llama-server on YOUR machine. Also writes results/environment.json."""
import argparse
from ecaps import environment
from ecaps.backend import LlamaServerBackend

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    a = ap.parse_args()
    environment.save()
    b = LlamaServerBackend(a.url)
    if not b.healthy():
        raise SystemExit(f"No llama-server reachable at {a.url}. Start one first (see README).")
    r = b.generate("The capital of Nigeria is", max_tokens=16, seed=1)
    print(f"{r.text!r}\n{r.n_tokens} tokens, {r.tokens_per_s:.1f} tok/s, ttft {r.ttft_s:.2f}s")
