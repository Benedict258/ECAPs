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
