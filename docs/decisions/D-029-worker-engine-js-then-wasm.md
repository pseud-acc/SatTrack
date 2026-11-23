# D-029 JavaScript SGP4 in the worker now; WASM when shadow dimming lands

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the viewer's worker · **Tier:** full

## Context
satellite.js 7.1.0 offers the same SGP4 code compiled to JavaScript and to WebAssembly. Both run in the worker (D-015)
and match Python sgp4 within 9.5 m.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **JS now behind `compute(dates)`; WASM when shadow dimming lands** | Correct failures (NaN), strict CSP, easy debugging now; bulk speed when needed | A later switch with its own tests | Shadows, passes and replays get WASM's bulk calculators |
| WASM now | 2–3× faster; less battery | Silent (0, 0, 0) on failure; `'wasm-unsafe-eval'`; import-map workaround in workers | – |
| JS only | Simplest | Slower bulk work on phones later | – |

## Decision
The worker hides the engine behind `compute(dates) → positions`. 3.2 ships the JavaScript `propagate()`. Switch to the
WASM `BulkPropagator` when day/night shadow dimming is built (D-028), or earlier if a real phone shows high-speed play
degrading.

## Evidence
Spike, 22 Nov: a full pass over 32,652 objects takes 51.5 ms in JS and 20.1 ms in WASM on the laptop (payloads: ~33 and
14 ms). Five objects fail SGP4 in Python (45544, 59878, 101148 error 1; 33818, 54569 decayed); JS returns NaN for them,
WASM returns (0, 0, 0). Area-by-area tally: JS 7, WASM 8, tie 9 (decision rounds page).

## Consequences
The switch adds a zero-vector guard, a parity-test row and `'wasm-unsafe-eval'` in the CSP. In a worker, import maps
don't apply: import the runtime from `dist/wasm/runtimes/single-thread-runtime.js` and the module from
`wasm-build/base-release/index.js` by path.

## Revisit when
- Shadow dimming is built (planned trigger).
- A phone shows high-speed play degrading.

## Related
D-014, D-015, D-027, D-028.
