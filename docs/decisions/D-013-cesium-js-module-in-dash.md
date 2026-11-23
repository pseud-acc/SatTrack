# D-013 Cesium runs as a JS module inside the Dash page

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE (spike 3.1)
**Component:** the tracker page (`app/`, `static/viewer/`) · **Tier:** full

## Context
Phase 3 replaces the Plotly 3D and 2D figures with a CesiumJS globe. Dash keeps the sidebar, list view, routing and
detail panel. The viewer needs the filter spec from Dash and has to report the selected object back.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Plain JS module in `static/viewer/`, wired by clientside callbacks and two `dcc.Store`s** | Whole Cesium API; no npm toolchain; one document | Viewer logic sits outside Dash's callback tests | Hover, paths, labels, search, PNG, shadows all use the Cesium API directly |
| Custom Dash component (React) | Dash-native props | An npm build in the repo, CI and the Heroku build | Same features, more build to maintain |
| Separate page in an iframe | Full isolation | Two documents in memory on phones; selection sync over `postMessage` | Shareable links and the bottom sheet get harder |

## Decision
Dash renders an empty `html.Div(id="globe")` that no callback ever writes to. `static/viewer/` code, loaded only on the
tracker page, mounts the viewer in it. Filters go in through a `dcc.Store` and a clientside callback; a click comes out
through `dash_clientside.set_props` on a second store, which server callbacks read for the detail panel and list.

## Evidence
The spike page (`docs/cesium-spike/`) runs the same Cesium code any of the options would run, so frame rate doesn't
separate them.

## Consequences
A test asserts that no callback outputs to the globe div. Viewer logic is tested with Playwright against state the
viewer exposes (counts, selection, engine, timings). Viewer code never goes in `assets/`, which Dash adds to every page.

## Revisit when
- A viewer feature needs two-way state Dash stores can't carry cleanly (e.g. many selected objects).
- Dash ships a supported way to mount third-party canvases that removes the clientside glue.

## Related
D-014, D-021, D-024; roadmap 3.2–3.6.
