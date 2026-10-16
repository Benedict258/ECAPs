# Design notes

ECAPs Node Runtime: **research prototype**. Wraps llama.cpp; no custom silicon.

## Decisions on ambiguous points (simplest honest option)
- **Cloud-built code, local measurement.** Development happened in a cloud container using `MockBackend`.
  Mock timings are not measurements. Real numbers only come from `python -m bench.run_all` on the owner's PC.
- **Dummy output is separate.** Anything produced with the mock goes to `results_dummy/` and is watermarked DUMMY.
  `results/` is reserved for real runs.
- **No HTTP deps.** The llama-server backend uses stdlib `urllib` to keep dependencies to psutil, matplotlib, pytest.
- **Git author.** Commits are authored as Benedict Isaac with no AI attribution (Honesty Rule 8).
