# ECAPs Node Runtime

> **Research and development stage. This is a prototype.**
> ECAPs (Edge Computing Agentic Processors) hardware does not exist yet; there is no ECAPs silicon.
> This repo is the *software runtime* that would run on such a node. Any benchmark here is meant to be measured on a
> **stand-in reference PC** (CPU-only), not on ECAPs hardware.
>
> **No real benchmark results have been produced yet.** All code was developed and tested on a labelled mock backend.
> The real run happens on the owner's PC with `python -m bench.run_all` (see below).

A small Python runtime that runs local AI agents (sense → plan → act) on a CPU-only machine by wrapping
[llama.cpp](https://github.com/ggml-org/llama.cpp). It does **not** claim to be faster than llama.cpp: the overhead
benchmark exists to show the wrapper adds little. Energy is **not measured**; "CPU-seconds per task" is only a proxy.
The memory budget is a **software setting**, not a change to physical RAM.

## Status: what is built / what is not

| Item | Status | How far it is verified |
|---|---|---|
| llama.cpp backend (`llama-server` over HTTP) | built | never run against a real server in development; first real use is on the owner's PC |
| Mock backend | built | used for all tests; every mock output is labelled DUMMY |
| Environment capture, model manager (auto-fit) | built | unit-tested; formula from the project brief |
| Agent runtime (validated JSON actions, SQLite memory) | built | tested with the mock; cloud LLM fallback is a stub, **off** |
| Benchmarks B1 overhead, B2 auto-fit, B3 offline loop, B4 power modes + figures F1–F4 + `summary.md` | built | pipeline verified on mock data only; **no real numbers yet** |
| Power modes (eco/normal/boost, simulated battery/solar) | built | unit-tested; eco's 64-token cap is a placeholder to re-check on real models |
| Preflight (`python -m bench.preflight`) | built | tested with temporary files; checks only, never downloads |
| Device interface: simulated feed (default) | built | tested |
| Device interface: serial / ESP32 | built | **fake port only**; the example sketch in `docs/ESP32.md` has **not been compiled or run** |
| Device interface: MQTT (optional `paho-mqtt`) | built | **in-memory fake broker only**; never run against a real broker |
| Management API (`/status` `/models` `/metrics`) | built | functional tests; read-only, loopback by default, no authentication |
| Offline-first outbox (local SQLite queue, optional cloud sync) | built | tests prove the local loop works with the network blocked and nothing goes out unless configured; sync tested against a **localhost** server only; cloud endpoint is a stub, **off** by default |
| Node discovery + request routing (UDP broadcast, hand-off to a less-busy peer) | built (prototype) | **tested on localhost only** (several processes on 127.0.0.1); not a real LAN; throughput gain not measured. More nodes serve more users; a model is **not** split across nodes |
| Proposed node spec (`docs/NODE_SPEC_PROPOSED.md`) | document | **proposed arithmetic, not measurements** |
| Real benchmark numbers and poster figures | **not produced yet** | run `bench.run_all` on a real PC |
| Splitting one model across nodes, authentication/TLS for the cluster and device links | not built | |

### Still unverified
- No real model has been run through this code.
- The ESP32 sketch has not been compiled; the serial adapter was tested only against a fake port.
- The MQTT adapter was tested only against a fake broker.
- Discovery and routing were tested on localhost only.
- Model licences are unverified (`docs/MODELS.md`).
- No power or energy was measured; no energy saving is claimed.

## Quick start (no model needed)
    pip install -r requirements.txt
    pytest
    python -m bench.run_all --mock     # plumbing check; writes DUMMY output to results_dummy/ (git-ignored)
    python -m ecaps.model_manager --budget-gb 4
    python -m ecaps.api --mock         # management API on http://127.0.0.1:8700 (DUMMY backend)

## How to run the real benchmarks on your PC
Full step-by-step guide for Windows: **`docs/RUN_ON_PC.md`**. In short:
1. `pip install -r requirements.txt` (Python 3.11+).
2. Put a CPU `llama-server` binary at `bin/` (or pass `--llama-server`), and the GGUF files named in `docs/MODELS.md` in `models/`.
   Download the **smallest model first**; nothing is downloaded for you. Check each model's licence.
3. `python -m bench.preflight --only b1,b3` (checks only), then `python -m bench.run_all --only b1,b3`.
4. After downloading the other models: `python -m bench.run_all --only b2`, then `--only b4`
   (or one `python -m bench.run_all` for everything). Real mode needs at least 5 repeats.
5. Outputs: `results/environment.json`, raw `results/*.json`, `results/figures/` (PNG 300 dpi + SVG, with hardware/date/model/commit footers)
   and `results/summary.md` (every number, captions, and an "Unverified" list). Nothing is typed by hand.

`results_dummy/` holds mock output only. It is watermarked DUMMY and must never be used on the poster.

## Optional pieces
- Serial/ESP32: `docs/ESP32.md`. MQTT: topic scheme in `ecaps/mqtt_device.py`. Select a device in `ecaps.config.json` (`"device"`).
- Cloud sync is **off**. It only runs if `ecaps.config.json` sets `"cloud": {"enabled": true, "url": "..."}`.
- Cluster prototype (localhost-tested): `python -m ecaps.cluster --id A --port 8801 --discovery-port 47801 --mock`.

## Layout
    ecaps/    backend, model_manager, agent, tools, memory, power, node, devices, mqtt_device, outbox, cluster, api, spec_calc
    bench/    run_all, preflight, b1..b4, figures, summary
    docs/     DESIGN.md, MODELS.md, ESP32.md, RUN_ON_PC.md, NODE_SPEC_PROPOSED.md
    tests/    pytest suite (mock backend, fake serial port, fake MQTT broker, localhost cluster)

License: MIT (see `LICENSE`).
