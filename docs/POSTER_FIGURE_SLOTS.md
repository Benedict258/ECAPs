# Poster figure slots

**Status: no real results exist yet.** These slots stay empty until the benchmarks are run on the stand-in reference PC.
Nothing on the poster may be filled from `results_dummy/`, from the mock backend, or by typing numbers by hand.

## Result slots

All commands are run from the repo root on the **real PC** (setup: `docs/RUN_ON_PC.md`). Each writes into `results/`.
Figures are generated only from the results JSON; their titles are computed from the data, so a weak result produces a title that says so. Do not edit them.

| Slot | Message (title is computed from the data) | Command that produces it | Output files | Experiment needs |
|---|---|---|---|---|
| F1 overhead | runtime overhead vs raw llama-server, with spread | `python -m bench.run_all --only b1` | `results/figures/F1_overhead.png` / `.svg` | smallest model |
| F2 auto-fit | how many software budgets (2, 4, 7 GB) the picked model stayed under; naive largest model alongside | `python -m bench.run_all --only b2` | `results/figures/F2_autofit.png` / `.svg` | all three models |
| F3 offline vs online | tasks correct and latency with the network allowed vs blocked | `python -m bench.run_all --only b3` | `results/figures/F3_offline.png` / `.svg` | smallest model |
| F4 power modes | tokens/s, wall time, success and CPU-seconds per task (an energy **proxy**) per mode | `python -m bench.run_all --only b4` | `results/figures/F4_power_modes.png` / `.svg` | smallest + budget-pick model |

- `python -m bench.run_all` with no `--only` runs all four. Every run re-renders all figures that have data and rewrites `results/summary.md`.
- To re-render from existing results without running any benchmark: `python -m bench.figures`.
- Every number used, a ready caption per figure, and the "measured on" line are in `results/summary.md`.
- The same repo also makes concept diagrams that contain **no results**: `python -m assets.make_diagrams` (outputs in `assets/diagrams/`: node family,
  software stack, edge-cloud collaboration). These are not result slots, and the software-stack one is also written to `results/figures/software_stack.*`.

## Footer every result figure must carry
Printed on the figure itself by `bench/figures.py` (check it is legible at poster size):

`Measured on: <CPU model>, <RAM> GB RAM, <OS>, CPU-only | <date> | commit <runtime commit hash> | models: <model names>` plus a slot-specific note:

| Slot | Extra text in the footer |
|---|---|
| F1 | `threads=<n>` |
| F2 | `software memory budget (not a change to physical RAM)` |
| F3 | `outbound attempts while blocked: <n>; repeats=<n>` |
| F4 | `repeats=<n>; CPU-seconds = energy proxy only, no watts measured` |

Wording rules for captions (also in `results/summary.md`): never say or imply faster than llama.cpp; never claim energy or watts saved;
say the memory budget is a software setting; say the machine is a stand-in reference PC, not ECAPs hardware.

## DUMMY rule
**DUMMY-stamped images are never printed, shown on the poster, or put in slides.** A file is DUMMY if any of these is true:
- it lives under `results_dummy/` (git-ignored; produced by `python -m bench.run_all --mock`);
- it has the large red "DUMMY DATA (mock backend)" watermark;
- its footer starts with "DUMMY RUN in a cloud container";
- the matching `summary.md` starts with "DUMMY DATA from MockBackend".
`python -m bench.check_results` checks these bookkeeping flags on `results/` and fails if anything is marked DUMMY. It cannot judge whether the numbers are good.

## Checklist: dropping real figures in after the PC run
1. Working tree is clean (`git status`) and you ran from the commit you intend to cite; the footer's commit hash comes from the checkout.
2. `python -m bench.preflight` printed PASS before the run (and for B2, other apps were closed).
3. All four experiments were run (or the empty slots are consciously left out; `summary.md` lists anything "not run").
4. `python -m bench.check_results` prints `RESULT: PASS`.
5. Open every PNG: no DUMMY watermark, footer shows **your PC's** CPU, RAM, OS, the date and the commit hash, model names are the ones you ran.
6. Read `results/summary.md` end to end and compare each figure's numbers with the tables. Keep failures as reported (for example "17/20 correct", an `under budget: False`).
7. Check F2: if a pick went over its budget, the title says so; do not retitle it.
8. Check F4 and any caption: "CPU-seconds is an energy proxy", no watts, no energy-saving claim.
9. Copy the SVG (preferred) or the 300 dpi PNG into the poster layout; do not re-type any number. Copy `results/` aside before rerunning anything.
10. Add the "Unverified or not measured" items from `summary.md` to the poster's small print or keep the QR code pointing to the README that lists them.
