# D-027 A measured performance budget for the viewer

**Status:** Accepted · **Date:** 2026-11-22 (provisional), accepted 2026-11-23 after the real-phone run · **PRs:** #SPIKE
**Component:** the viewer; its tests and release checks · **Tier:** full

## Context
Phase 3's "done when" said "smooth on a mid-range laptop", which no check can fail. The spike measured frame rate,
main-thread work, first positions and heap on a laptop with the CPU throttled 4× and 6×.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Budget from the spike's numbers with margins** | A regression fails a check | Throttling isn't a phone; no margin on the 4× payloads fps | Each feature PR reports its cost against the margin |
| Fixed round targets (e.g. 30 fps everywhere) | Simple | Not tied to measurements | – |
| No budget | No work | Regressions found by users | – |

## Decision
| Target | Budget | Measured in the spike |
|---|---|---|
| Laptop frame rate, all objects | 60 fps | 60 |
| Laptop main-thread work a frame | ≤ 5 ms | 2.9 ms |
| Laptop first positions | ≤ 1.5 s | 0.84 s |
| 4× CPU, payloads | ≥ 24 fps, ≤ 2 s | 24 fps, 1.25 s |
| 6× CPU, all objects | ≥ 20 fps | 24–26 fps |
| Main-thread heap | ≤ 80 MB | 31–52 MB |
| Phones | 30 fps cap | – |

If frames stay below 20 fps for 5 s with space junk mode on, the viewer suggests switching debris off; it never does it
itself (D-016).

## Evidence
Spike matrix (`docs/cesium-architecture.md`, 22 Nov). Real phone (Adreno 740, 23 Nov): 59–60 fps uncapped with payloads
and with all objects; main thread 1.6–2.8 ms; first positions 0.9–1.2 s. Within every target.

## Consequences
CI has no GPU: main-thread time, load time and heap are CI checks; frame rates are a release step on the reference
laptop (median of 3 runs, 2 fps tolerance). Raising the budget needs a decision entry. Heat over minutes of use wasn't
tested; the phone cap and the triggers below cover it.

## Revisit when
- A real mid-range phone runs below 24 fps on payloads: lower `resolutionScale`, then consider GPU interpolation.
- A feature pushes laptop main-thread work over 5 ms: profile first.
- High-speed play stutters on a phone: switch to WASM (D-029).
- The catalogue passes ~45k objects: re-run the matrix.
- Users report heat or battery drain: render only on change while paused; lower the phone cap to 24 fps.

## Related
D-015, D-016, D-023, D-029.
