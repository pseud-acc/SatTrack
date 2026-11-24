# D-042 CI checks the viewer's start-up with fixed budgets and a same-runner comparison against the target branch

**Status:** Accepted (owner, 2026-11-24) · **Date:** 2026-11-23 · **PRs:** roadmap 3.2 (`feature/cesium-viewer`)
**Component:** the viewer's browser tests (`tests/e2e/test_viewer.py`, `tests/e2e/conftest.py`) and
`.github/workflows/app-e2e.yml` · **Tier:** full (decides what gates every viewer PR)

## Context
D-027 sets first positions at <= 1.5 s on the reference laptop and says CI checks main-thread time, load time and heap.
GitHub's runners have no GPU: Chromium renders the globe in software on the same 4 CPUs the propagation worker uses.
CI measured 1.40, 1.94 and 1.98 s where the laptop measured 0.84-1.48 s. The first proposal, failing above a fixed
3.0 s, would let start-up degrade by up to 50% without failing or being noticed (owner's challenge, 24 Nov 2026): raw
wall-clock time on a shared runner is a weak signal.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| Fail above 3.0 s, median of 3 | Simple; not flaky | A 1.5-3 s drift passes unseen | – |
| Fail above 1.5 s | The budget as written | Failed 2 of 2 CI runs | – |
| Warn only above 1.5 s | Never flaky | Easy to ignore | – |
| **Full set: fixed budgets that don't depend on runner speed, plus cold visits to this branch and the target branch interleaved on the same runner, compared phase by phase, plus a job summary table** | Runner speed cancels out; a failure names the phase; catches work and download growth directly | ~2 min more CI; no baseline until the target branch has the viewer | Every later Phase 3 PR (3.3-3.11) is measured against main |
| Calibrated timing (a fixed benchmark on the runner) | No second app | Only approximates the software-rendering cost | – |
| Two propagation workers to get CI under 1.5 s | Faster on multi-core devices | Optimises for CI; a design change outside 3.2 | Possible after 3.11 |

## Decision
The full set.

1. **Fixed budgets** (`test_budget_full_catalogue`, full-size synthetic catalogue of 32,652 objects, payloads shown,
   median of 3 first visits):
   - bytes received (as sent, compressed) before the first positions <= 5 MB;
   - records the worker builds before the first positions == the payload count (only the shown types first);
   - heap after load <= 80 MB and main thread <= 5 ms a frame (D-027);
   - first positions <= 3.0 s, kept as a backstop and as the only timing limit when there is no baseline;
   - long main-thread tasks before the first positions: reported, not a limit.
2. **Same-runner comparison** (`test_startup_against_baseline`): on pull requests, CI checks out the target branch into
   `baseline/`; the tests start it on the same full-size data with its own pinned vendor files. Three cold visits to
   each app, interleaved and alternating which goes first. Each side's median visit (by first positions) is compared
   phase by phase (data fetched and parsed, Cesium loaded, globe created, records built and first samples, first
   positions). A phase fails when it is over 20% **and** over 150 ms slower than the baseline. Bytes are reported.
3. **Job summary**: both tables go to the CI job summary on every run, and to pytest's warnings summary.

D-027's 1.5 s stays the release check on the reference laptop, run before each change to the flag's default.

## Evidence
- CI, 23 Nov: first positions 1.40, 1.94, 1.98 s; main thread 2.3 ms a frame; heap 69 MB.
- Laptop, 24 Nov, fixed budgets: 3.95-4.03 MB before first positions; 19,742 records built; heap 54.7-74.6 MB
  (garbage collection timing moves it); main thread 3.6-3.8 ms a frame (5.15 ms in space junk mode once, while
  three apps and Chromium shared the laptop; 3.15 ms alone).
- Laptop, 24 Nov, this branch against itself as the baseline (checks the comparison end to end): every phase within
  -12% to -6%, bytes identical.
- CI, 24 Nov, PR #76 (docs only, so identical code): the comparison failed twice, the branch +40% on records built
  and first positions. Per-visit figures (PR #79, 3 CI runs) showed no steady gap between the apps and no effect of
  which app goes first. Instead, single visits on CI fall into a fast or a slow mode about 45% apart (e.g. 1,302 and
  1,370 ms against 1,928-2,062 ms in one run), on either app. With 3 visits, a median can land in different modes
  on the two sides, which gives a +40% "regression" on identical code. The harness was also unbalanced (the branch
  went first in 2 of 3 rounds, took the slot right after the budget test's heavy page in that test's browser, and
  the baseline's first visit hit a cold server). PR #79 removes the imbalance (a fresh browser, one discarded
  warm-up visit to each app, 4 visits each in ABBA ABBA order, lower-middle visit compared; limits unchanged) and
  passed twice on CI (+2%, +3%). The two-mode spread is not removed: the owner decides on a further step.
- CI, 24-25 Nov, why the two modes (PR #79 diagnostics, 3 runs, ~80 visits with worker timestamps, /proc and
  Chrome traces): not CPU contention or throttling. Steal was 0% and idle ~25% in both modes, and the worker posted
  its "ready" at the same time (0.6-1.1 s) in fast and slow visits. The slow mode is the main thread handling that
  message one ~400-700 ms task later. The tasks in the way are Plotly's, on the same page: evaluating
  plotly.min.js (~400 ms) and the 3D graph's pick-buffer `readPixels` (380-670 ms, a synchronous read that waits
  for the software GPU, which is busy with the globe). The viewer's own point creation (~450-500 ms) is the third.
  Whether one of them runs before the message depends on load order, which changes from visit to visit.
  `--disable-renderer-backgrounding` and its timer flags didn't remove it: 8 of 8 visits fast in one run (3 of 8
  without the flags), 4 of 10 in another (0 of 10 without).

## Consequences
- The e2e job runs ~2 minutes longer on pull requests and downloads the baseline's vendor tarballs (a little more
  since PR #79: 10 comparison visits instead of 6).
- The comparison runs in its own browser with warm-up visits and an order-balanced sequence; changing the visit
  count or order must keep both sides in the same slots (PR #76's failure came from an unbalanced harness).
- #70 itself has no baseline (main has no viewer); its gate is the fixed budgets. Issue #72 tracks the remaining gaps:
  gradual drift across many PRs (an anchored baseline), data growth (a pipeline size check and a field-cost limit) and
  #70's laptop figures as the first anchor.
- The baseline runs in this branch's Python environment; a baseline that needs other packages fails the comparison,
  which then needs a look.

## Revisit when
- Issue #72's anchored baseline lands (adds a third app to the comparison).
- The heap measurement reaches 80 MB on a run without changes: measure after a forced garbage collection instead.
- GitHub runners gain GPUs: tighten the ceiling towards 1.5 s.

## Related
D-015, D-027, D-037; roadmap 3.2; issue #72.
