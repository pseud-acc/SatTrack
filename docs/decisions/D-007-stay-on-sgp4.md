# D-007 Stay on SGP4; improve accuracy through fresher elements

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** recorded in #57 from the analysis in #56
**Component:** propagation (server now, browser from Phase 3) · **Tier:** full

## Context
With OMM propagation and WGS 84 display in place (D-004, D-006), the remaining ISS error against NASA's ephemeris was
about 1 km and growing with element age. The question was whether a different propagator would do better.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Stay on SGP4; fresher elements** (several runs a day, SupGP) | GP elements are fitted for SGP4; works in Python and the browser (satellite.js) alike | Accuracy limited by element age | Plans 4.1–4.3; satellite.js in Phase 3 matches Python sgp4 within 9.5 m (3.1 spike) |
| SGP4-XP | Better long-range accuracy | Needs its own element sets and a licensed binary library | No browser build |
| A numerical propagator | Higher fidelity | GP elements would be misread; heavy | – |
| Operator ephemerides (OEM) | Best for the objects covered | A few hundred objects for a few days | Possible for a handful of objects in pass prediction |

## Decision
Keep SGP4. Improve accuracy with fresher element sets (plan 4.1) and SupGP (plans 4.2–4.3).

## Evidence
ISS against NASA's ephemeris, element set of 21 Nov 04:54 UTC: 0.75 km median at 0–12 h after epoch, 1.13 km at
12–24 h, 1.52 km at 24–36 h, 1.98 km at 36–48 h (#56). Element age is the main source of error.

## Consequences
Every positional feature is SGP4 from GP/SupGP elements; the browser and server must agree (Phase 3 parity test).
The ±1-day time scrubber (Cesium decisions) follows from the error growing with age.

## Revisit when
- Pass prediction (Phase 7): OEM for a few objects such as the ISS from NASA.
- A free, browser-capable SGP4-XP becomes available.

## Related
D-003, D-004, D-006; roadmap Phase 4, Phase 7; the Cesium architecture.
