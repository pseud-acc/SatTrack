"""
Cesium globe tab (roadmap 3.2), shown only when the viewer flag is on (app/core/viewer.py).

div#globe is empty and no callback ever writes to it (D-013): static/viewer/viewer.js mounts Cesium inside it.
The stores carry state across the Dash/viewer boundary:
- viewer-config: same-origin URLs of the viewer module, worker, Cesium and satellite.js (set at page render).
- viewer-selection: the selected object, written by the viewer with dash_clientside.set_props in roadmap 3.4.
- viewer-bridge: the clientside bridge's status ("loading", "mounting", "mounted"), for tests.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

GLOBE_ID = "globe"
VIEWER_STORES = ("viewer-config", "viewer-selection", "viewer-bridge")   # the filter spec is the page's filter-spec store


def create_globe_tab(config):
    return dbc.Tab([
        html.Div(id=GLOBE_ID),
        dcc.Store(id="viewer-config", data=config),
        dcc.Store(id="viewer-selection", data=None),
        dcc.Store(id="viewer-bridge", data=None),
    ], label="Globe", tab_id="globe")
