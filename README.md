# ECAPs Node Runtime

**Status: research and development prototype.** Software only; no ECAPs silicon exists.
Benchmarks (when run) are measured on a stand-in reference PC, not ECAPs hardware.
Wraps llama.cpp; it does not claim to be faster than llama.cpp.

## Run
    pip install -r requirements.txt
    pytest
    python -m ecaps.environment      # writes results/environment.json

## Benchmarks
    python -m bench.run_all          # real run on your PC (needs llama-server + GGUFs, see docs/MODELS.md)
    python -m bench.run_all --mock   # plumbing check only; writes DUMMY output to results_dummy/ (git-ignored)
Real results go to `results/` (raw JSON, figures, `summary.md`). Power is not measured; no energy claims are made.
Memory budgets are a software setting, not a change to physical RAM.
