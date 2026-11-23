# D-019 Single selection with per-satellite toggles

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #68
**Component:** the viewer · **Tier:** light

## Context
Today a click adds an orbit path; several can be shown and one button clears them. Cesium can draw paths, follow a
satellite and show a ground track.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **One selection; panel toggles for orbit path (3D), follow camera (3D), ground track (2D)** | Each behaviour is the user's choice | No multi-select yet | Shareable links carry one satellite (D-024) |
| Select one, pin many | Today's multi-path view | More state, more UI | – |
| Fixed behaviour on click | Simplest | Takes control away from the user | – |

## Decision
One selected satellite at a time. Its panel has three toggles: orbit path (one period, past faded; 3D), follow camera
(3D) and ground track (switches the view to 2D).

## Evidence
The owner's call.

## Consequences
The ground-track toggle relies on one viewer handling 2D (D-021).

## Revisit when
Users ask to compare several satellites (multi-select).

## Related
D-021, D-024.
