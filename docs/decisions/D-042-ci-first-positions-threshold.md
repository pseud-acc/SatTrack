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

### First anchor: viewer-baseline-1 (#70 merge, aebef417a386cec032f50f0538718ff2848ac935)
Annotated tag `viewer-baseline-1` (issue #72, item 3): Cesium 1.147.0 with the D-041 eval patch, satellite.js 7.1.0.
Measured 24 Nov 2026, 02:08-02:13 UTC, on the reference laptop (D-027: Intel Core i7-1355U, Intel Iris Xe; it also has
an RTX 3050). `test_budget_full_catalogue` run three separate times at the tag; each run is itself the median of
3 first visits. The tests' headless Chromium renders in software (SwiftShader), so these are not frame-rate figures.

| Figure (full-size catalogue, payloads shown) | Run 1 | Run 2 | Run 3 | Median | Range |
|---|---|---|---|---|---|
| Bytes before first positions | 4.18 MB | 4.07 MB | 4.06 MB | 4.07 MB | 4.06-4.18 MB |
| Records built before first positions | 19,742 | 19,742 | 19,742 | 19,742 | – |
| Heap after load | 60.7 MB | 58.3 MB | 68.6 MB | 60.7 MB | 58.3-68.6 MB |
| Main thread per frame | 6.34 ms | 8.24 ms | 2.67 ms | 6.34 ms | 2.67-8.24 ms |
| First positions | 2,893 ms | 2,603 ms | 2,914 ms | 2,893 ms | 2,603-2,914 ms |
| Long main-thread tasks before first positions | 6 | 7 | 7 | 7 | 6-7 |
| Longest of those tasks | 1,225 ms | 947 ms | 1,181 ms | 1,181 ms | 947-1,225 ms |
| Phase: data fetched + parsed | 1,530 ms | 712 ms | 2,212 ms | 1,530 ms | 712-2,212 ms |
| Phase: Cesium loaded | 614 ms | 465 ms | 355 ms | 465 ms | 355-614 ms |
| Phase: globe created | 673 ms | 525 ms | 514 ms | 525 ms | 514-673 ms |
| Phase: records built + first samples | 2,885 ms | 2,596 ms | 2,906 ms | 2,885 ms | 2,596-2,906 ms |
| Worker per pass (payloads) | 694 ms | 480 ms | 272 ms | 480 ms | 272-694 ms |
| Test result | fail (main thread) | fail (main thread) | pass | | |

Run 3 also reached space junk mode (runs 1 and 2 stopped at the main-thread check): 32,140 shown, main thread
3.78 ms a frame, heap 55.7 MB.

Machine state before each run (16 GB RAM): free memory 0.35, 1.42 and 1.22 GB; CPU load 43%, 36% and 91%;
26 Chromium/Chrome and 11 Edge processes open. Other work was running on the laptop at the same time (the main chat's
local app and Chromium, another agent editing docs).

Comparison on the tag (`SATTRACK_BASELINE_DIR` set to the same checkout, one run, free memory 0.41 GB, CPU 80%):
the table works end to end and bytes were identical (4.06 MB both sides), but the run failed. Data fetched + parsed
was 775 ms against 1,598 ms (+106%) with the same code on both sides; the other phases were +3% to +17%. In the same
run the fixed-budget test put first positions at 3,265 ms, over the 3.0 s ceiling. With identical code, these failures
come from the load on the laptop, not from the viewer.

**Caveat.** These figures are a first anchor taken on a busy laptop, not D-027's release check. They are slower and
noisier than the earlier laptop figures (first positions about 2.9 s against 0.84-1.48 s in Context; main thread 2.7-8.2 ms a
frame against 3.6-3.8 ms). Re-measure on a quiet machine before the flag is turned on in production.

## Consequences
- The e2e job runs ~2 minutes longer on pull requests and downloads the baseline's vendor tarballs.
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
