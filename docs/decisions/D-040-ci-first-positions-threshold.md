# D-040 CI checks first positions against twice the laptop budget

**Status:** Proposed (owner to confirm) · **Date:** 2026-11-23 · **PRs:** roadmap 3.2 (`feature/cesium-viewer`)
**Component:** the viewer's browser tests (`tests/e2e/test_viewer.py`) · **Tier:** light (a test constant)

## Context
D-027 sets first positions at ≤ 1.5 s on the reference laptop and says CI checks main-thread time, load time and
heap; raising a budget needs a decision entry. GitHub's runners have no GPU: Chromium renders the globe with SwiftShader
on the same 4 CPUs the propagation worker uses, so the worker builds its records and first samples more slowly than on
any device with a GPU.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **CI fails above 3.0 s (2× the budget), median of 3 first visits; 1.5 s stays the release check on the laptop** | Catches real regressions (a 2× slowdown); not flaky on shared runners | A 1.5–3 s regression on fast hardware shows only in the release check and in the logged figure | Every later PR reports the figure in CI's warnings summary |
| CI at 1.5 s | The budget as written | Failed 2 of 2 CI runs (1.55 s; median 1.94 s) while the laptop measured 0.84–1.48 s | – |
| Defer rendering until the first positions | Faster in CI | A black canvas for a second for real users, to suit the test | – |
| Two propagation workers | Faster on multi-core devices | Several hours; a design change outside 3.2 | Possible later if phones need it (D-015) |

## Decision (proposed)
`FIRST_POSITIONS_CI_MS = 3000`, checked on the median of three first visits to a full-size synthetic catalogue (32,652
objects) served by the app with Brotli. Main thread (≤ 5 ms a frame) and heap (≤ 80 MB) stay at the D-027 budget in CI.
The test logs every figure.

## Evidence
CI, 23 Nov: first positions 1.40, 1.94 and 1.98 s (main thread 2.3 ms a frame, heap 69 MB). Laptop (software WebGL as
well): 0.84, 0.86 and 1.22 s, and 1.28–1.48 s in single runs.

## Consequences
The release check on the reference laptop remains the gate for the 1.5 s budget.

## Revisit when
- GitHub runners gain GPUs or become faster: tighten towards 1.5 s.
- The figure in CI drifts above 2.5 s: profile the worker's start-up before raising anything.

## Related
D-015, D-027; roadmap 3.2.
