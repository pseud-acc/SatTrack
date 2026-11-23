# D-015 Propagate in a Web Worker and interpolate on the main thread

**Status:** Accepted · **Date:** 2026-11-22 (provisional), accepted 2026-11-23 after the real-phone run · **PRs:** #SPIKE
**Component:** the viewer · **Tier:** full

## Context
Propagating all 32,652 objects takes 19–30 ms a pass on a laptop's main thread; phones are roughly 4–6× slower, which
would leave little of a 16 ms frame for Cesium.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Worker on a time grid, linear interpolation on the main thread, adaptive step (0.25–10 s sim time)** | Main thread does ~2–3 ms a frame; degrades gracefully; handles fast play | ~3–4 days to build; a time jump waits one worker pass | Labels' nearest-N search and shadows run in the worker |
| Main thread every frame | Simplest | 2–11 fps at 4–6× CPU | – |
| Worker at a fixed 1 Hz | Simpler controller | Fast play and slow devices degrade badly | – |
| Two code paths by device | Tuned per device | Double testing | – |

## Decision
A Web Worker loads the data, builds the satellite.js records and computes positions on a fixed grid of simulation time;
the main thread interpolates linearly between the two samples around the current time. A small controller widens the
step when worker passes or frames are slow, or play speed is high. The engine is D-029.

## Evidence
- Interpolation error: midpoint error s²/8R, about 1 m at 1 s and 110 m at 10 s in low orbit, against ~15 km a pixel
  at a whole-globe view.
- Laptop, throttled CPU (spike, 22 Nov): with the worker 20–32 fps and first positions in 1–1.7 s at 4–6×, against
  2–11 fps and 3–12 s on the main thread. Heap 31–52 MB against 79–133 MB.
- Real phone (Adreno 740, 23 Nov, owner's screenshots): 59–60 fps uncapped with payloads (19,742) and with all
  objects (32,652); main thread 1.6–2.8 ms a frame; worker 22–50 ms a pass; first positions 0.9–1.2 s.
- Parity: every engine within 9.5 m of Python sgp4 (99th percentile 7.4 m).

## Consequences
The worker exposes engine, interval, pass time and counts for tests. Failed objects are NaN and hidden. The phone was
high-end, so the throttled runs remain the stand-in for mid-range and low-end devices (D-027).

## Revisit when
- A mid-range or low-end phone runs below 24 fps on payloads: lower `resolutionScale`, then consider interpolation on
  the GPU (~1–2 weeks).
- The catalogue passes ~45k objects: re-run the spike matrix.

## Related
D-027, D-029; `docs/cesium-architecture.md`.
