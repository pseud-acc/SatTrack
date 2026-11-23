# D-006 Show WGS 84 geodetic latitude and altitude

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #56
**Component:** `helper__satellite_position.py` (2D map, hover labels, list view) · **Tier:** light

## Context
Positions were converted to geocentric latitude and height above a 6,378.137 km sphere. Checked against outside data,
the ISS was about 19 km off on the map and up to 13 km low in altitude.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Geodetic latitude, height above the WGS 84 ellipsoid** (Kelso's iteration, vectorised) | Matches maps and other trackers; reproduces another SGP4 tracker exactly with the same TLE | A small iteration per point | Cesium works in WGS 84 natively (Phase 3); pass prediction (Phase 7) needs geodetic observer coordinates |
| Keep the sphere | No change | ~19 km display error at mid-latitudes | – |

## Decision
Geodetic latitude and WGS 84 height; longitude unchanged. The Plotly 3D globe still draws a sphere, with points placed
by geodetic latitude to match the map texture.

## Evidence
- Same TLE as wheretheiss.at: identical latitude, longitude and altitude (0.00 km ground distance, was 19.2 km).
- Against NASA's ISS ephemeris at 10 times: displayed position 18.8 → 0.97 km (median), 20.2 → 1.79 km (max).
- Tests: the forward WGS 84 formula takes each (lat, alt) back to the position to 1 mm; the published axes check the
  equator and poles.

## Consequences
Heights above 60° latitude rise by more than 10 km against the old values.

## Revisit when
- Cesium replaces Plotly (Phase 3): positions are drawn in Earth-fixed coordinates and Cesium handles the ellipsoid;
  the server conversion remains for the list view and hover text until 3.6.

## Related
D-004, D-007; the Cesium architecture (`docs/cesium-architecture.md`).
