# Design notes

ECAPs Node Runtime: **research prototype**. Wraps llama.cpp; no custom silicon.

## Decisions on ambiguous points (simplest honest option)
- **Cloud-built code, local measurement.** Development happened in a cloud container using `MockBackend`.
  Mock timings are not measurements. Real numbers only come from `python -m bench.run_all` on the owner's PC.
- **Dummy output is separate.** Anything produced with the mock goes to `results_dummy/` and is watermarked DUMMY.
  `results/` is reserved for real runs.
- **No HTTP deps.** The llama-server backend uses stdlib `urllib` to keep dependencies to psutil, matplotlib, pytest.
- **Git author.** Commits are authored as Benedict Isaac with no AI attribution (Honesty Rule 8).
- **Memory estimate follows the brief literally** (4-bit = 0.5 bytes/weight). Real Q4_K_M files are closer to ~0.6 bytes/weight,
  so B2 measures peak RSS and reports honestly whether each pick stays under budget.
- **Model tiers**: Qwen2.5-1.5B / Phi-3.5-mini (3.8B) / Qwen2.5-7B, chosen for permissive licences (Apache-2.0 / MIT).
  Qwen2.5-3B is skipped on purpose (research licence). Licences are UNVERIFIED: the cloud sandbox cannot reach Hugging Face.

## Stretch work (power modes, devices, management API)
- **Power modes.** `eco` = smallest tier, 1/4 of physical cores, 32 max tokens, ctx 1024. `normal` = largest tier fitting the
  memory budget, 1/2 cores, 64 tokens, ctx 2048. `boost` = same tier as normal, all physical cores, 128 tokens, ctx 4096.
  So at a 4 GB budget normal and boost differ in threads/tokens/context but not model tier. Chosen as the simplest rule;
  the numbers are design settings, not tuned results. Mode is chosen from a **simulated** battery % with plain thresholds
  (<30 eco, >=80 boost, >=60 boost if solar is on), no hysteresis, so it can flap near a threshold.
- **B4 and energy.** B4 reports tokens/s, wall time, task success and CPU-seconds per task (user+system CPU of the server plus
  the client process, via psutil). It is an energy **proxy**; no watts are measured and no energy saving is claimed.
  Eco's 32-token cap may truncate JSON actions on real models; if so it will show up as lower task success, and is reported as is.
  Per-step tokens/s is over very short outputs, so it is noisy.
- **Device interface.** Default = `SimulatedSensors` (static values or a scripted sequence). `SerialSensors` speaks the line protocol in
  `docs/ESP32.md` and needs the optional `pyserial`. It is tested only against an in-memory fake port. If a device is silent or answers
  `ERR`, the action is reported as failed and node state is not updated (no faked success). Command arguments reject newlines.
- **Management API.** Stdlib `http.server`, read-only JSON (`GET /status /models /metrics`), loopback by default, **no authentication**.
  `/status` serves cached sensor values from the last agent step so API calls never touch the serial port concurrently.
  `/models` sizes are the manager's estimates, not measurements. Not benchmarked.
- **Thread safety.** The node loop may run in a worker thread, so the SQLite memory uses `check_same_thread=False` plus a lock
  (found by running the CLI in mock mode; there is a regression test).
- **Out of scope this session** (not built): node discovery/routing, offline sync queue, MQTT adapter.
- **Mock realism.** The mock does not model mode differences (threads/context) in speed or CPU, so dummy B4 bars look similar
  across modes. That is expected; real differences can only come from the owner's run.
