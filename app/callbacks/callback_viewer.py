"""
The clientside bridge between Dash and the Cesium viewer (roadmap 3.2, D-013). Registered only when the viewer flag
is on (app/core/viewer.py), so with it off the page carries no viewer code at all.

When the tracker page renders its viewer stores, the bridge records the config and filters on
window.sattrackViewerBridge and, the first time, adds static/viewer/viewer.js as a module script (the only way the
viewer code is loaded: never from assets/, which Dash serves on every page). Once loaded, the viewer mounts into
div#globe; later store changes go straight to window.sattrackViewer.mount(). The output, viewer-bridge, holds the
status for tests. No callback ever outputs to div#globe.
"""
from dash import Input, Output

BRIDGE = """
function(config, filters) {
    var bridge = window.sattrackViewerBridge = window.sattrackViewerBridge || {};
    bridge.config = config;
    bridge.filters = filters;
    if (!config) { return "no-config"; }
    if (window.sattrackViewer && window.sattrackViewer.mount) {
        return window.sattrackViewer.mount(config, filters);
    }
    if (!document.getElementById("sattrack-viewer-module")) {
        var s = document.createElement("script");
        s.type = "module";
        s.id = "sattrack-viewer-module";
        s.src = config.module;
        document.head.appendChild(s);
    }
    return "loading";
}
"""


def register(app):
    app.clientside_callback(
        BRIDGE,
        Output("viewer-bridge", "data"),
        Input("viewer-config", "data"),
        Input("viewer-filters", "data"),
    )
