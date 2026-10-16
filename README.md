# ECAPs Node Runtime

> **Research and development stage. This is a prototype.**
> ECAPs (Edge Computing Agentic Processors) hardware does not exist yet; there is no ECAPs silicon.
> This repo is the *software runtime* that would run on such a node. Any benchmark here is measured on a
> **stand-in reference PC** (CPU-only), not on ECAPs hardware.

A small Python runtime that runs local AI agents (sense → plan → act) on a CPU-only machine by wrapping
[llama.cpp](https://github.com/ggml-org/llama.cpp). It does **not** claim to be faster than llama.cpp: the overhead
benchmark exists to show the wrapper adds little. Energy is **not measured**; "CPU-seconds per task" is only a proxy.
The memory budget is a **software setting**, not a change to physical RAM.

## Status: what is built / what is not

| Item | Status | Notes |
|---|---|---|
| llama.cpp backend (`llama-server` over HTTP) + mock backend | built | real backend only exercised on the owner's PC |
| Environment capture (`results/environment.json`) | built | auto-detected, nothing assumed |
| Model manager (auto-fit to a memory budget) | built | formula + overhead + 1 GB OS headroom; picks reasoned in output |
| Agent runtime (tools, validated JSON actions, SQLite memory) | built | cloud fallback is a stub, **off** by default |
| B1 overhead, B2 auto-fit, B3 offline loop | built, **not yet run for real** | code verified on a labelled mock only |
| Power modes eco/normal/boost (simulated battery/solar) + B4 | built, **not yet run for real** | CPU-seconds = energy proxy only |
| Device interface: simulated feed (default) | built, tested | |
| Device interface: serial / ESP32 adapter | built, tested on a **fake port only** | not tested with a real ESP32; see `docs/ESP32.md` (sketch untested) |
| Management API (`/status` `/models` `/metrics`) | built, tested | read-only, loopback by default, no authentication |
| Real benchmark numbers and poster figures | **not produced yet** | run `bench.run_all` on a real PC |
| MQTT adapter | not built | |
| Offline-first sync queue | not built | |
| Node discovery / request routing | not built | |
| Model licences | **unverified** | see `docs/MODELS.md` |

## Quick start (no model needed)
    pip install -r requirements.txt
    pytest
    python -m bench.run_all --mock     # plumbing check; writes DUMMY output to results_dummy/ (git-ignored)
    python -m ecaps.model_manager --budget-gb 4
    python -m ecaps.api --mock         # management API on http://127.0.0.1:8700 (DUMMY backend)

## How to run the real benchmarks on your PC
1. `pip install -r requirements.txt` (Python 3.11+).
2. Get a CPU `llama-server` binary from the llama.cpp releases and put it at `bin/llama-server` (`.exe` on Windows),
   or set the `LLAMA_SERVER` environment variable to its path.
3. Download three GGUF models into `models/` with the exact names in `docs/MODELS.md` (about 8 GB in total, estimated).
   Check each model's licence on its model card first.
4. Optional smoke test: start `llama-server` yourself, then `python -m ecaps.smoke`.
5. Run everything with one command: `python -m bench.run_all` (at least 5 repeats; temperature 0; fixed seeds).
   It refuses to start, and downloads nothing, if the binary or models are missing.
6. Outputs: `results/environment.json`, raw `results/*.json`, `results/figures/` (PNG 300 dpi + SVG, with hardware/date/model/commit footers)
   and `results/summary.md` (every number, captions, and a "Not run" list). Nothing in these files is typed by hand.

`results_dummy/` holds mock output only. It is watermarked DUMMY and must never be used on the poster.

## Layout
    ecaps/    backend, model_manager, agent, tools, memory, power, node, devices, api
    bench/    run_all, b1..b4, figures, summary
    docs/     DESIGN.md, MODELS.md, ESP32.md
    tests/    pytest suite (mock backend, fake serial port)

License: MIT (see `LICENSE`).
