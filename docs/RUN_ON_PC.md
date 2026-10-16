# Running the real benchmarks on your PC

Target machine for this guide: **Windows, Intel i5, 8 GB RAM, CPU-only**. Commands are PowerShell.
Nothing in this repo downloads models or binaries for you. The author of this guide has **not** run the real benchmarks:
the code was developed and tested against a mock backend, so timings below are described by *what the code does*, not by measured durations.

Everything the benchmarks write comes from measurement. Never edit numbers in `results/` by hand.

## 0. What will be measured (so you know what to expect)
| Experiment | What the code does |
|---|---|
| B1 overhead | 1 smallest model, 1 warm-up (discarded) + 5 repeats x 2 paths (raw llama-server vs runtime), 64 tokens each |
| B3 offline loop | smallest model, 20 tasks x 5 repeats x 2 modes (network allowed / outbound blocked) = 200 agent steps |
| B2 auto-fit | budgets 2, 4, 7 GB; for each, load the auto-fit model and the largest model: **6 model loads**, 5 generations of 48 tokens each |
| B4 power modes | eco / normal / boost, 20 tasks x 5 repeats each = 300 agent steps, plus one model load per mode |

The slowest parts are loading models (B2, B4). Model files are read from disk each time, so a slow disk makes those steps slow.

## 1. Python
1. Install Python 3.11 or newer from python.org (tick "Add python.exe to PATH").
2. In PowerShell, in the repo folder:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   pip install -r requirements.txt
   pytest                             # should pass before you benchmark anything
   ```

## 2. llama-server (prebuilt CPU binary)
1. Open the llama.cpp releases page on GitHub (`ggml-org/llama.cpp`, Releases).
2. Download the **Windows CPU build for x64** (a `.zip`). Release file names change between versions (look for `win` and `cpu`,
   or `avx2`, and `x64`). Do **not** pick the CUDA, Vulkan, HIP or ARM builds. (File names are from memory and unverified: check the page.)
3. Unzip it so that `llama-server.exe` and its `.dll` files sit together, e.g. in the repo's `bin\` folder.
4. If you put it elsewhere, tell the runtime where it is, either per run with `--llama-server C:\path\llama-server.exe`
   or once per session with `$env:LLAMA_SERVER = "C:\path\llama-server.exe"`.
5. Windows Firewall may ask about `llama-server.exe`. The runtime starts it bound to `127.0.0.1` (this PC only); it should work
   if you decline network access, though that is an expectation, not something tested here.
6. Licence: llama.cpp is believed to be MIT. Verify on the repository.

## 3. Models (GGUF files)
Read `docs/MODELS.md` first. Files must be placed in `models\` with **exactly** these names (or point elsewhere with `--models-dir`):

| Tier | File name | Est. size |
|---|---|---|
| small | `qwen2.5-1.5b-instruct-Q4_K_M.gguf` | ~0.9 GB |
| mid | `phi-3.5-mini-instruct-Q4_K_M.gguf` | ~2.3 GB |
| large | `qwen2.5-7b-instruct-Q4_K_M.gguf` | ~4.6 GB |

Sizes are estimates (parameters x 0.6 bytes); check the real size on the download page.
Download the Q4_K_M GGUF from the Hugging Face repos listed in `docs/MODELS.md`, then rename to the names above.
Some repos split large models into several shard files (`...-00001-of-00002.gguf`); if so, merge them with `llama-gguf-split --merge`
(shipped in the llama.cpp release zip) or use a repo that offers a single file. **Check every model's licence on its model card first**; they are unverified here.

**Download the smallest model first** and run steps 4-5 before downloading the others. The other two together are several GB; if your
bandwidth is limited, only fetch them once the first results look sane.

## 4. Preflight (checks only, downloads nothing)
```powershell
python -m bench.preflight --only b1,b3
```
Fix every `[FAIL]` line. A `[WARN]` about RAM or swap means: close browsers, chat apps and IDEs, and leave the PC idle. It also checks
that each GGUF file has a valid header (a truncated download fails).

## 5. Run order
Results files accumulate between runs; `results\summary.md` and the figures are regenerated each time from whatever results exist.

1. **Smallest model: B1 and B3**
   ```powershell
   python -m bench.run_all --only b1,b3
   ```
   Look at `results\summary.md` and `results\figures\`. If something looks wrong (errors, 0 tasks correct), fix it before going on.
2. **Download the other two models**, then check: `python -m bench.preflight --only b2`
3. **B2 with all three models.** Close every other application first, and do not use the PC while it runs.
   ```powershell
   python -m bench.run_all --only b2
   ```
4. **B4 power modes**
   ```powershell
   python -m bench.run_all --only b4
   ```
`python -m bench.run_all` with no `--only` runs everything in one go once all models are present. Real mode always uses at least 5 repeats.

Settings you may change in `ecaps.config.json`: `budget_gb` (used by B4's normal/boost tier) and `quant`.
Do not run `--mock` and expect it to touch `results\`: mock output goes to `results_dummy\` and is watermarked DUMMY.

## 6. Expected behaviour while it runs
- A `llama-server.exe` process starts and stops for each model load; do not start your own on port 8089.
- During B3's "network blocked" mode the runtime refuses any non-loopback connection and records attempts; the summary shows the count (expected 0).
- B2's "naive largest model" runs *do* load the 7B model even at the 2 GB and 4 GB budgets, because the budget is only a software setting.
  On an 8 GB machine this may be slow or may swap. That is the point of the comparison; it is reported as it happens.
- The first line of output is the preflight checklist. If it says FAIL, nothing runs.

## 7. Reading `results\summary.md`
- Top line: **"Measured on"** (CPU, RAM, OS, date, commit) as auto-detected. Every figure carries the same footer.
- B1: tokens/s, time to first token and peak RSS for the raw server and via the runtime, plus overhead %. A positive overhead means the runtime was slower. Small is the goal; faster than raw would be noise, not a feature.
- B2: for each budget, the model picked, peak RSS, and whether it stayed under the budget (`under budget` True/False). A False is a real result: report it.
- B3: tasks correct out of 20 per repeat, both modes, latency, outbound attempts, and the list of failed tasks. Small models make mistakes; the failures are kept.
- B4: tokens/s, wall time, task success and **CPU-seconds per task**. CPU-seconds is only an energy proxy; no watts were measured, so do not claim energy savings.
- "Not run" at the bottom lists anything without a results file, and the things this prototype does not have.
- Raw per-run data is in `results\*.json`; the figures are in `results\figures\` (PNG 300 dpi and SVG).

## 8. Troubleshooting
| Symptom | Likely cause / what to do |
|---|---|
| `RESULT: FAIL` from preflight | read the `[FAIL]` lines: missing binary/model, bad GGUF header (re-download), or low disk |
| `llama-server exited early` | not enough free memory, wrong binary build, or a bad model file. Close other apps, run the preflight, try the binary by hand: `bin\llama-server.exe -m models\<file> -c 1024` and read its message |
| `llama-server did not become healthy` | the model is still loading from a slow disk, or port 8089 is in use. Close other programs using that port; retry |
| Out of memory / PC freezes during B2 | the 7B loads even at small budgets (see section 6). Close everything else. If the PC still cannot do it, stop, and report that result honestly rather than hiding it |
| Very low tokens/s, disk light constantly on | **swapping**: the model does not fit in free RAM. Check Task Manager > Memory. Close apps, reboot, or accept that the number reflects swapping and say so |
| Runs are very slow | normal for CPU-only 7B on a laptop. Do not reduce repeats below 5. Run steps separately (section 5), plug in the charger and set the power plan to high performance so clock speeds are not throttled |
| Results vary a lot between repeats | background load or thermal throttling; the spread is reported in the summary. Rerun later with the PC idle, and keep the first results if you rerun (copy `results\` aside) |
| `pytest` fails | do not benchmark yet; send the output |

If something fails midway, results from experiments that already finished are kept; only the failed experiment needs re-running with `--only`.
