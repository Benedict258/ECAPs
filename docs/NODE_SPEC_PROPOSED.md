# ECAPs node specification: PROPOSED

> **PROPOSED. Not measured.** Every number here is Benedict's design arithmetic, or the result of the formulas below applied to
> proposed inputs. No ECAPs hardware exists, nothing in this document was benchmarked, and power figures are design targets,
> not measurements. The tables below are printed by `python -m ecaps.spec_calc` (tested in `tests/test_spec_calc.py`) so the arithmetic is reproducible.

## Formulas
- weights (GB) = parameters (billions) x bytes per weight; 16-bit = 2, 8-bit = 1, 4-bit = 0.5
- memory needed (GB) = weights x 1.25 (runtime and KV-cache overhead); the model manager adds about 1 GB more for the OS
- tokens/s ceiling = memory bandwidth (GB/s) / weights (GB)

## What the ceiling means (and does not)
Decoding one token of a dense model reads all weights once, so bandwidth / weights is an **upper bound** for one user, one stream.
Real speed is expected to be lower: it ignores KV-cache traffic, compute limits, software efficiency and thermal limits.
Quantisation changes this too (a real Q4_K_M file is larger than 0.5 bytes per weight). It is a reasoning tool for choosing memory
bandwidth, not a performance claim. A future check on the stand-in PC could compare measured B1 tokens/s with its ceiling, once its
memory bandwidth is known; that has not been done.

## Draft table (proposed)
| Node | Models | Memory | Bandwidth | Power (target) | Users (target) |
|---|---|---|---|---|---|
| Node Mini | 1-3B at 4-bit | 2-4 GB | about 25-50 GB/s | 3-5 W | one host board (e.g. ESP32) |
| Node | about 7B at 4-bit | 8 GB | about 100 GB/s | 10-25 W | 1-5 users |
| Node Hub | 13-30B at 4-bit | 32 GB | 200+ GB/s | 40-60 W | many users via batching |

## The formulas applied to the draft table
| Node | model size (4-bit) | weights GB | x1.25 GB | + 1 GB OS headroom GB | proposed memory GB | bandwidth GB/s | tokens/s ceiling |
|---|---|---|---|---|---|---|---|
| Node Mini | 1B to 3B | 0.5 to 1.5 | 0.62 to 1.88 | 1.62 to 2.88 | 2-4 | 25 to 50 | 16.7 to 100.0 |
| Node | 7B | 3.5 | 4.38 | 5.38 | 8 | 100 | 28.6 |
| Node Hub | 13B to 30B | 6.5 to 15.0 | 8.12 to 18.75 | 9.12 to 19.75 | 32 | 200 | 13.3 to 30.8 |

Reading it: the 7B Node needs 4.38 GB with overhead (5.38 GB with OS headroom), which fits the proposed 8 GB. Its ceiling is
100 / 3.5 = 28.6 tokens/s (stated as "about 28" in the draft). The 30B Hub needs 18.75 GB (19.75 GB with headroom) in 32 GB, with a ceiling of
200 / 15 = 13.3 tokens/s ("about 13"). The Mini's ceiling ranges widely (16.7 to 100 tokens/s) because 1B and 3B models and
25 and 50 GB/s bandwidth are both in range; the low end is a 3B model at 25 GB/s, the high end a 1B model at 50 GB/s.
The Hub's "many users via batching" and the Node's "1-5 users" are targets: batching trades per-user speed for total throughput,
and none of this has been measured or built.

## Solar sizing example (illustrative)
Example for a continuously running 20 W node, with the assumptions stated:
```
daily energy = 20 W x 24 h = 480 Wh/day
battery = 480 / 0.8 = 600 Wh
panel = 480 / (5 x 0.7) = 137.1 W

```
Assumptions, all of which are placeholders to replace with sourced values:
- the node draws a constant 20 W for 24 h (a real duty cycle may be lower or higher);
- **5 peak-sun-hours per day is an assumption. The figure for Minna must be sourced** (for example from a solar-resource dataset) and the sizing redone;
- 0.7 combined efficiency for panel, charge controller and wiring losses, and 0.8 usable battery fraction (this depends on battery chemistry and age);
- one day of autonomy only (no cloudy-day margin), no inverter losses, no temperature derating, no margin for panel ageing.

The 137 W panel and 600 Wh battery are therefore example sizes under those assumptions, not a recommendation. A 20 W power figure is itself
a proposed target; it has not been measured on any hardware.

## Open items
- Verify power draw by measurement on real hardware (not possible on the stand-in PC without a power meter; this repo does not measure watts).
- Source sun-hours for the deployment site.
- Measure real memory bandwidth and compare against the ceiling.
- Check the users-per-node targets with a real batching test.
