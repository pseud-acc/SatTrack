# D-005 Build each propagator once per element set

**Status:** Accepted · **Date:** 2026-11-21 · **PRs:** #56
**Component:** `helper__satellite_position.py` · **Tier:** light

## Context
Building an sgp4 `Satrec` costs about 15× more than propagating it, and every callback rebuilt all of them. Orbit paths
rebuilt the Satrec at every time step.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Cache per worker, keyed by catalogue number + every value the Satrec is built from** | Callbacks only propagate; a corrected element set republished with the same epoch can't be served stale | ~20 MB per worker | Plan 4.1 reloads data while running: the cache clears itself above 100,000 entries |
| Key by (satellite, epoch) | Smaller key | Serves a stale propagator when a corrected set keeps its epoch (Copilot review) | – |
| Vectorised construction | Faster build | sgp4 builds one propagator per call; the cache already takes construction out of callbacks | – |
| No cache | Simple | 188 ms per callback | – |

## Decision
Build the cache at start-up and propagate all satellites in one `SatrecArray` call; orbit paths build once and use
`sgp4_array`. `state.py` logs how many came from OMM, TLE or neither.

## Evidence
Live-sized file (19,740 satellites), laptop: all satellites per callback 188 → 116 ms; 2D ground track (3,600 points)
71 → 42 ms; 3D orbit (720 points) 25 → 12 ms. About 20 MB per worker.

## Consequences
Tests cover revised elements at the same epoch, a changed TLE line 2, and rows without elements not growing the cache.

## Revisit when
- Phase 3.6 removes server-side propagation from the request path: the cache may only be needed by tests.
- Plan 4.1's in-process reload lands: confirm the 100,000-entry reset is adequate.

## Related
D-004; roadmap 3.6, 4.1.
