"""
Cesium globe tab (roadmap 3.2), shown only when the viewer flag is on (app/core/viewer.py).

No callback ever writes to div#globe (D-013): static/viewer/viewer.js mounts Cesium inside it. It holds only the
loading bar (D-052; owner, 27 Nov 2026), rendered with the page so it shows before any script has run; the viewer
fills one bar per start-up step and hides it once the satellites are placed.
The stores carry state across the Dash/viewer boundary:
- viewer-config: same-origin URLs of the viewer module, worker, Cesium and satellite.js (set at page render).
- viewer-selection: the selected object, written by the viewer with dash_clientside.set_props in roadmap 3.4.
- viewer-bridge: the clientside bridge's status ("loading", "mounting", "mounted"), for tests.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

GLOBE_ID = "globe"
VIEWER_STORES = ("viewer-config", "viewer-selection", "viewer-bridge")   # the filter spec is the page's filter-spec store


def loading_bar():
    return html.Div([
        html.Div([html.Span(className="sattrack-loading-bar") for _ in range(4)], className="sattrack-loading-bars"),
        html.Div("Loading the globe…", className="sattrack-loading-text"),
    ], className="sattrack-loading", role="status", **{"aria-live": "polite"})


def create_globe_tab(config):
    return dbc.Tab([
        html.Div(loading_bar(), id=GLOBE_ID),
        dcc.Store(id="viewer-config", data=config),
        dcc.Store(id="viewer-selection", data=None),
        dcc.Store(id="viewer-bridge", data=None),
    ], label="Globe", tab_id="globe")
