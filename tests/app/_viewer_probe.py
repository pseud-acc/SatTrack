"""Import the app as gunicorn does (with whatever SATTRACK_CESIUM_VIEWER / SATTRACK_VENDOR_DIR the caller set) and
print one JSON line describing what it serves. Run by tests/app/_viewer_support.py in its own process."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO_ROOT), str(Path(__file__).parent)]

import plotly  # noqa: E402

import run_app  # noqa: E402
from _support import layout_by_id  # noqa: E402

client = run_app.server.test_client()
tracker = run_app.display_page("/sat_visualisation")
components = layout_by_id(tracker)
globe = components.get("globe")
pages = {}
for path in ("/", "/sat_visualisation"):
    resp = client.get(path)
    pages[path] = {"status": resp.status_code, "html": resp.get_data(as_text=True), "headers": dict(resp.headers)}
vendor = client.get("/static/vendor/cesium-1.147.0/index.js", headers={"Accept-Encoding": "br"})
print(json.dumps({
    "dependencies": json.loads(client.get("/_dash-dependencies").data),
    "tracker_ids": sorted(components),
    "globe_children": None if globe is None else json.loads(json.dumps(getattr(globe, "children", None),
                                                                          cls=plotly.utils.PlotlyJSONEncoder)),
    "active_tab": getattr(components.get("sat-viz-tabs"), "active_tab", None),
    "type_filter_hidden": getattr(components.get("type-filter"), "hidden", None),
    "viewer_config": getattr(components.get("viewer-config"), "data", None),
    "pages": pages,
    "vendor": {"status": vendor.status_code, "headers": dict(vendor.headers)},
}))
