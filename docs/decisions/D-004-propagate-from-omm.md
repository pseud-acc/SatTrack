# D-004 Propagate from OMM; keep TLE lines as a one-release fallback

**Status:** Accepted · **Date:** 2026-11-21 · **PRs:** #54 (plan 1.2), #56 (plan 1.3)
**Component:** app export (`app__satcat_tle.sql`) and `helper__satellite_position.py` · **Tier:** full

## Context
TLE lines can't hold catalogue numbers above 339,999 (Alpha-5's limit). SupGP is published only as OMM, and the
browser propagator planned for Phase 3 (satellite.js) reads OMM directly.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **OMM fields, TLE fallback for one release** | Removes the catalogue ceiling; the format every later phase uses; safe rollout in either order | Two code paths for one release | SupGP (4.2), the browser (Phase 3, `json2satrec`), six-digit catalogue numbers |
| Stay on TLE lines | No change | Hard ceiling at 339,999; SupGP unusable | Blocks 4.2 and Phase 3's OMM route |
| OMM only, no fallback | One path | A pre-OMM file or an incomplete row loses positions on rollout | – |

## Decision
Export every field `sgp4.omm.initialize` reads (12 new columns, `Epoch` formatted `%Y-%m-%dT%H:%M:%S.%f`) and build
each propagator from OMM. TLE lines are used only when a row has no complete OMM set, for one release. A satellite
without TLE lines is still exported. Catalogue numbers above 339,999 are built with satnum 0, which is only a label;
the app keeps the real `SatCatId`.

## Evidence
- Positions, 19,736 satellites, propagated to 21 Nov 18:00 UTC, TLE (main) vs OMM: median 0.00 m, 95th 0.74 m, 99th
  5.6 m, max 236 m (STARLINK-38452, high drag, OMM's extra digits of B* and eccentricity). 12,300 within 1 mm; no SGP4
  error-code changes. At epoch ±24 h the gap was at most 29 m (#54).
- ISS against NASA's ephemeris: OMM and TLE within 0.2 m of each other, both median 1.13 km from NASA.
- Eccentricity differs in 4,024 rows by up to 5e-8 (OMM 8 decimals, TLE 7).

## Consequences
The app reads both the 17- and 29-column files. DataFrame memory 15.2 → 20.2 MB per worker. The TLE fallback is to be
removed after one release.

## Revisit when
- The TLE fallback has served its release: remove it (and the `TLE1`/`TLE2` columns when nothing reads them).
- Space-Track changes its OMM field set.

## Related
D-003, D-005, D-007, D-009; roadmap 1.2–1.4.
