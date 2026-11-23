# D-020 Time scrubber of ±1 day

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #68
**Component:** the viewer · **Tier:** light

## Context
Today the view is always "now". In the browser, time becomes something the user controls; SGP4 accuracy falls with
distance from the element epoch.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Own scrubber, ±1 day, Now, play/pause, 1×–1000×** | Positions stay in the accurate part of each element set; fine slider control | A pass tomorrow evening may be out of reach | Replays from `element_history` later |
| ±3-day scrubber (recommended) | Covers more passes | Larger drift at the ends | – |
| Now-only controls | Simplest | No replay | – |
| Cesium's timeline widget | Free | Dated, poor on phones, unbounded | – |

## Decision
Our own scrubber covering ±1 day from now, with a Now button, play/pause and speeds 1×–1000×. Element age shows at the
displayed time.

## Evidence
SGP4 drift of roughly 1–3 km a day in low orbit; measured ISS error grows from 0.75 km in the first 12 h to ~2 km at
36–48 h (D-007). The owner chose ±1 day.

## Consequences
About 1.5–2 days to build. Shareable links outside the window open at "now" with a notice (D-024).

## Revisit when
Pass prediction (Phase 7) needs a longer look-ahead, or fresher elements (Phase 4) shrink drift.

## Related
D-007, D-024.
