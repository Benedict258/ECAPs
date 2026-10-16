# ECAPs Node Runtime

**Status: research and development prototype.** Software only; no ECAPs silicon exists.
Benchmarks (when run) are measured on a stand-in reference PC, not ECAPs hardware.
Wraps llama.cpp; it does not claim to be faster than llama.cpp.

## Run
    pip install -r requirements.txt
    pytest
    python -m ecaps.environment      # writes results/environment.json
