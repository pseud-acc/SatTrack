# D-021 One viewer for 3D, 2D and Columbus; retire the Plotly 2D tab

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the tracker page · **Tier:** light

## Context
Today's 2D tab shows one filtered satellite's ground track on a raster map. Cesium has 3D, 2D and Columbus scene modes
in one viewer.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **One viewer with a mode switch** | Every satellite in 2D; one renderer and one position path | PNG export must be rebuilt | Needed by D-019's ground-track toggle |
| Keep a separate 2D tab | Familiar | Two renderers and position paths | – |

## Decision
Cesium's scene modes replace both Plotly tabs. Every satellite shows in 2D.

## Evidence
Feature comparison in the review page (22 Nov).

## Consequences
PNG export rebuilt from the canvas (D-028). Ground tracks split at ±180°. Plotly's 3D/2D callbacks go in 3.6.

## Revisit when
–

## Related
D-013, D-019, D-028.
