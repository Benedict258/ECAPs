# ECAPs Node Runtime: Build Brief for Claude Code

Owner: Benedict Isaac. Purpose: a working reference software stack plus honest, reproducible benchmark results (with figures) for a conference poster (BUILD26, Build26/5P, Abuja, 21-22 Oct 2026).

Read this whole file before writing code. Follow the **Honesty Rules** strictly. They matter more than any feature.

---

## 1. Context

ECAPs (Edge Computing Agentic Processors) is an edge-AI node family at **research and development stage**. Nothing is simulated and no custom silicon exists. One architecture and one software stack come in three sizes (working names):

- **Node Mini:** plug-in compute module for robotics/engineering systems; a host board (e.g. ESP32) senses and actuates.
- **Node:** compact unit for homes/institutions (CPU-only reference here).
- **Node Hub:** shared community node, nodes can be networked.

This repo is the **ECAPs Node Runtime**: the software layer that would run on any of them. Benchmarks run on Benedict's PC as a **stand-in reference node**. They are not ECAPs hardware results and must never be presented as such.

"Agentic" means the node runs local AI agents that sense, decide and act on sensors/machines without waiting for the cloud.

---

## 2. Honesty Rules (non-negotiable)

1. Every number in any figure, table or README comes from a results file produced by the benchmark scripts. **Never type results by hand. Never invent, round up or "expect" numbers.**
2. Every figure and results table carries a footer: measured hardware (auto-detected CPU model, RAM, OS, CPU-only), date, model names, runtime commit hash.
3. We wrap llama.cpp. **Do not claim to be faster than llama.cpp.** The overhead test exists to show the runtime adds little, not to beat it.
4. We cannot measure watts. Report **CPU-seconds per task** and tokens/s only, labelled as a proxy. Do not claim energy saved.
5. The memory budget is a **software setting**, not a change to real RAM. Say so in captions.
6. Report failures and bad results as they are (e.g. "17/20 tasks correct"). No cherry-picking runs. Keep raw results.
7. Small models make mistakes. Do not hide that.
8. Do not add `Co-Authored-By` or any AI attribution lines to git commits or PRs. Author is Benedict Isaac.
9. Before downloading anything larger than 1 GB (models), tell Benedict the size and ask. Prefer reusing files already on disk. Bandwidth may be limited.
10. Verify the licence of every model and library used. Prefer permissive licences. Record them in `docs/MODELS.md`. Do not make N-ATLAS the default; it can be an optional adapter later after checking its size and licence.

---

## 3. Hardware and environment

Expected: Intel Core i5, 8 GB RAM (about 7 GB usable), no GPU, likely Windows. **Detect everything yourself** (CPU model, core/thread count, RAM, OS) and save to `results/environment.json`. Do not assume.

Optional: an ESP32 may be available. It is not guaranteed. The device interface must work with a **simulated sensor feed** by default, and with a real ESP32 over serial if present.

---

## 4. Tech choices

- Language: Python 3.11+, with `psutil`, `matplotlib`, `pytest`. Keep dependencies few.
- Inference backend: **llama.cpp**. Preferred: prebuilt CPU `llama-server` binary driven over HTTP (avoids compilers on Windows). Fallback: `llama-cpp-python`. Put it behind a `Backend` interface so either works.
- Models: GGUF, quantized (Q4_K_M main; Q8_0 for one quantization comparison if time allows). Use three size tiers, e.g. about 1B, 3B, 7B instruct models. Pick specific models yourself, check licences, and record them. Use structured/JSON-constrained output (grammar) for agent actions to improve reliability.
- Everything runs fully offline after models are downloaded.

---

## 5. Scope, in priority order

Work in this order. After each stage the repo must run and tests must pass. Commit at each stage.

**Core (must have)**
1. **Setup and environment capture:** repo skeleton, backend adapter, `environment.json`, smoke test that generates text locally.
2. **Model manager (auto-fit):** given a memory budget in GB, choose the largest model tier that fits. Estimate: `weights_GB = params_B x bytes_per_weight` (16-bit 2, 8-bit 1, 4-bit 0.5), then `x 1.25` for runtime/KV overhead, plus about 1 GB headroom for the OS. Return the choice and the reasoning. Expose via config and CLI.
3. **Agent runtime:** a sense -> plan -> act loop. Tools (e.g. `set_pump(on/off)`, `log_alert(msg)`, `read_sensor(name)`). The model returns a structured action; the runtime validates and executes it; a short persistent local memory (file/SQLite) stores recent events. Local-first. Cloud fallback is an optional pluggable stub, **off by default**.
4. **Benchmarks and figures** (Section 6).

**Stretch (only after core is done and verified)**
5. **Power-aware modes** (eco / normal / boost): change thread count, max output tokens, context size and model tier. Driven by a simulated battery/solar level input.
6. **Device interface:** serial (ESP32) and/or MQTT adapter plus the simulated feed.
7. **Offline-first queue:** actions/events queued locally and synced if a cloud endpoint is configured.
8. **Node discovery and request routing:** simple LAN discovery so several nodes can share load (the "rack" idea). Scope claim: more nodes serve more users; do **not** split one model across nodes.
9. **Management API:** `GET /status`, `/models`, `/metrics` for a manager to monitor a node.

---

## 6. Benchmarks (these produce the poster results)

Run each experiment with fixed seeds, temperature 0 where applicable, **at least 5 repeats**, report mean and spread. Save raw data to `results/*.json`. Write `bench/` scripts so everything is reproducible with one command (`python -m bench.run_all`).

**B1. Overhead vs raw llama.cpp.** Same model, same prompt, same token count, same threads. Compare calling the backend directly (minimal script) vs through the runtime. Metrics: tokens/s, time to first token, peak RAM. Report % overhead with spread.

**B2. Memory auto-fit.** Budgets: 2, 4 and 7 GB (software setting). For each: which model the manager picks, its measured peak RSS, whether it stays under the budget, tokens/s. Compare against a naive "always load the largest (7B) model" that exceeds the small budgets. Show peak RSS vs budget line.

**B3. Offline agent loop.** A scripted set of about 20 deterministic tasks with checkable correct actions (e.g. given sensor readings, the correct tool call). Run it with network enabled and with the network blocked (test must also assert no outbound connection is attempted). Report success count (e.g. 17/20), latency per task, and both modes side by side.

**B4. Power modes** (if stretch 5 is done). For eco/normal/boost on the same task set: tokens/s, CPU-seconds per task, wall time, task success. Label CPU-seconds as an energy proxy only.

If a stretch item is not finished, do not fake its benchmark. Leave it out and say so in `results/summary.md`.

---

## 7. Poster figures

Generate from the results files with scripts in `bench/figures.py`. Output **PNG at 300 dpi and SVG** to `results/figures/`.

- One message per figure, with a statement-style title (e.g. "Runtime picks the model that fits the memory budget").
- Poster-readable: large fonts (at least 14 pt at figure size), strong contrast, restrained palette, colour-blind safe, direct labels over legends where possible, generous margins.
- Footer text on each figure: hardware, date, model, commit hash, "software memory budget" where relevant.
- Planned figures: F1 overhead bars; F2 auto-fit (budget vs chosen model and peak RSS); F3 offline vs online success and latency; F4 power modes. Also produce one clean software-stack diagram (SVG) showing: Device interface -> Agent runtime -> Model manager -> Backend (llama.cpp), plus Power manager, Memory, Management API, Node discovery.
- Write `results/summary.md`: every number used, a ready caption per figure, and the exact "measured on" line.

---

## 8. Repo layout (suggested)

```
ecaps-node-runtime/
  README.md            # 5-line pitch, status "research prototype", how to run, results preview
  LICENSE              # ask Benedict; MIT proposed
  docs/MODELS.md       # models, sizes, licences, download sources
  docs/DESIGN.md       # architecture and why (memory bandwidth per watt over TOPS)
  ecaps/               # runtime package (backend, model_manager, agent, tools, memory, power, devices, api)
  bench/               # run_all.py, b1..b4, figures.py
  tests/
  results/             # environment.json, raw json, figures/, summary.md
```

The README is the QR-code target. It must state plainly: research and development stage, prototype, measured on a stand-in reference machine, not ECAPs silicon.

---

## 9. Acceptance checklist

- [ ] `pytest` passes; smoke test generates text fully offline.
- [ ] Model manager returns the right tier for 2 / 4 / 7 GB budgets with explanations.
- [ ] Agent loop completes the task set offline; test asserts no outbound network calls.
- [ ] B1-B3 run end to end with one command; raw results saved; environment captured.
- [ ] Figures F1-F3 (+F4 if done) generated from results only, with footers.
- [ ] `results/summary.md` lists all numbers and captions.
- [ ] README is accurate and honest about stage and limits.
- [ ] No hand-typed results anywhere; no AI attribution in commits.

When something is ambiguous, pick the simplest honest option, note it in `docs/DESIGN.md`, and tell Benedict. Ask before large downloads or licence choices.
