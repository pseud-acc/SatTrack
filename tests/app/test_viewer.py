"""The Cesium viewer's server side (roadmap 3.2): the feature flag, the tracker layout, the vendor route and the
security headers. The browser side (positions, budget, CSP violations, off-site requests) is in tests/e2e.

- Flag off (this session's app, as production runs): nothing new on any page.
- Flag on: the app in its own process (_viewer_support.flag_on_app) with a stand-in vendor folder.
"""
import hashlib
import json

import pytest
from flask import Flask

from _support import REPO_ROOT, layout_by_id
from _viewer_support import flag_on_app, make_fake_vendor

from app.core import viewer as viewer_mod

VIEWER_IDS = {"globe", "viewer-config", "viewer-selection", "viewer-bridge"}   # filter-spec is page-level (3.3a)


# ---- switched off (SATTRACK_CESIUM_VIEWER=0) --------------------------------------------------------------------

def test_globe_on_by_default(monkeypatch):
    """D-052: the globe is on unless the variable switches it off (the Plotly 3D view was removed)."""
    monkeypatch.delenv("SATTRACK_CESIUM_VIEWER", raising=False)
    assert viewer_mod.flag_on() is True
    for value in ("0", "false", "off", "no", "OFF"):
        assert viewer_mod.flag_on({"SATTRACK_CESIUM_VIEWER": value}) is False
    for value in ("", "1", "true", "on", "YES"):
        assert viewer_mod.flag_on({"SATTRACK_CESIUM_VIEWER": value}) is True


def test_switched_off_never_reads_the_vendor_files(monkeypatch):
    """Switched off, nothing is paid at boot: no vendor file is read or hashed."""
    monkeypatch.setenv("SATTRACK_CESIUM_VIEWER", "0")
    monkeypatch.setattr(viewer_mod, "load_vendor", lambda *a, **k: pytest.fail("vendor files read with the flag off"))
    viewer_mod.reset_viewer_state()
    try:
        state = viewer_mod.viewer_state()
        assert state["enabled"] is False and state["manifest"] is None
    finally:
        viewer_mod.reset_viewer_state()


def test_switched_off_tracker_has_no_viewer(app_module, dependencies, client):
    """This session runs with SATTRACK_CESIUM_VIEWER=0 (tests/app/conftest.py): the tracker opens on the list."""
    tracker = layout_by_id(app_module.display_page("/sat_visualisation"))
    assert not VIEWER_IDS & set(tracker)
    assert tracker["sat-viz-tabs"].active_tab == "tbl-viz"
    # Only the globe draws rocket bodies and debris, so the type switches and junk mode are hidden without it
    assert tracker["type-filter"].hidden is True
    assert not [d for d in dependencies if "viewer" in d["output"] or "globe" in d["output"]]   # the filter toggle is clientside too (D-052)
    for path in ("/", "/sat_visualisation"):
        resp = client.get(path)
        html = resp.get_data(as_text=True)
        assert "static/viewer" not in html and "sattrackViewer" not in html
        assert "Content-Security-Policy-Report-Only" not in resp.headers
        assert "Strict-Transport-Security" not in resp.headers


# ---- flag on ----------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flag_on(tmp_path_factory):
    return flag_on_app(make_fake_vendor(tmp_path_factory.mktemp("vendor")))


def test_flag_on_tracker_mounts_the_globe_tab(flag_on):
    assert VIEWER_IDS <= set(flag_on["tracker_ids"])
    assert "filter-spec" in flag_on["tracker_ids"]   # the spec the bridge hands the viewer
    assert flag_on["active_tab"] == "globe"
    assert flag_on["type_filter_hidden"] is False   # the type switches and junk mode, which the globe can draw
    assert flag_on["globe_children"] is None   # the empty div Cesium mounts into (D-013)
    config = flag_on["viewer_config"]
    assert config["cesium"] == "/static/vendor/cesium-1.147.0/"
    assert config["satellite"] == "/static/vendor/satellite.js-7.1.0/"
    assert config["data"] == "/data/objects.json"
    for key in ("module", "worker", "css", "filterSpec"):
        assert config[key].startswith("/static/viewer/") and "?v=" in config[key]
    # every URL the viewer is given is same-origin (D-014: no third party at runtime)
    assert all(v.startswith("/") and not v.startswith("//") for v in config.values() if isinstance(v, str))
    # the browser's filter rules are the schema's (roadmap 3.3a; tests/e2e/test_filter_spec_browser.py checks them)
    from app.core.filter_spec import browser_rules
    assert config["specRules"] == browser_rules()


def test_no_callback_ever_outputs_to_the_globe(flag_on):
    """D-013: div#globe belongs to Cesium; a Dash update to it would wipe the viewer."""
    for d in flag_on["dependencies"]:
        outputs = d["output"].strip(".").split("...")
        assert not any(o.split(".")[0] == "globe" for o in outputs), d["output"]


def test_viewer_code_loads_only_through_the_bridge(flag_on):
    """The page shell (every page) carries only the bridge's inline function, never the viewer module itself: the
    module is added by the bridge when the tracker's stores render, and nothing comes from assets/."""
    for page in flag_on["pages"].values():
        assert page["status"] == 200
        assert "static/vendor" not in page["html"]
        assert '<script src="/static/viewer' not in page["html"]
    assert not list((REPO_ROOT / "assets").rglob("*viewer*"))


def test_flag_on_sends_report_only_csp_and_hsts(flag_on):
    headers = flag_on["pages"]["/sat_visualisation"]["headers"]
    assert "Content-Security-Policy" not in headers   # report-only first
    policy = dict(part.strip().split(" ", 1) for part in headers["Content-Security-Policy-Report-Only"].split(";"))
    assert policy["default-src"] == "'self'"
    assert policy["worker-src"] == "'self'"
    assert "'self'" in policy["script-src"].split()
    # D-041 option B: WebAssembly allowed (Cesium's meshoptimizer now, satellite.js's engine in 3.11), string eval never
    assert "'wasm-unsafe-eval'" in policy["script-src"].split()
    for banned in ("'unsafe-eval'", "'unsafe-inline'"):
        assert banned not in policy["script-src"].split()
    assert policy["object-src"] == "'none'"
    assert headers["Strict-Transport-Security"] == viewer_mod.HSTS
    assert "includeSubDomains" not in headers["Strict-Transport-Security"]


def test_csp_hashes_every_inline_script(flag_on):
    """Each inline script on the page (Dash's renderer and clientside callbacks, the analytics snippet) is allowed by
    its hash, so the policy reports nothing for the page's own scripts."""
    import base64
    import re
    page = flag_on["pages"]["/sat_visualisation"]
    allowed = set(page["headers"]["Content-Security-Policy-Report-Only"].split("script-src", 1)[1].split(";")[0].split())
    inline = re.findall(r"<script(?![^>]*\bsrc=)(?![^>]*application/json)[^>]*>(.*?)</script>", page["html"], re.S)
    assert inline
    for body in inline:
        digest = base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode()
        assert f"'sha256-{digest}'" in allowed, body[:80]


def test_flag_on_serves_vendor_files(flag_on):
    v = flag_on["vendor"]
    assert v["status"] == 200
    assert v["headers"]["Content-Encoding"] == "br"
    assert v["headers"]["Cache-Control"] == viewer_mod.IMMUTABLE


def test_flag_on_without_vendor_files_falls_back(tmp_path):
    """Fail closed: the flag on but no verified vendor files means no globe (the 2D map and list stay), no error."""
    probe = flag_on_app(tmp_path / "missing")
    assert not VIEWER_IDS & set(probe["tracker_ids"])
    assert probe["active_tab"] == "tbl-viz"


# ---- the vendor folder and route (stand-in files) ---------------------------------------------------------------

@pytest.fixture
def vendor(tmp_path):
    make_fake_vendor(tmp_path)
    manifest, reason = viewer_mod.load_vendor(tmp_path)
    assert reason is None
    return manifest


@pytest.fixture
def vendor_client(vendor, monkeypatch):
    monkeypatch.setattr(viewer_mod, "viewer_state", lambda: {"enabled": True, "manifest": vendor, "reason": None})
    server = Flask(__name__, static_folder=str(REPO_ROOT / "static"))
    viewer_mod.register_vendor_routes(server)
    return server.test_client()


def test_load_vendor_rejects_a_changed_file(tmp_path):
    make_fake_vendor(tmp_path)
    (tmp_path / "satellite.js-7.1.0/dist/io.js").write_bytes(b"export function json2satrec() { evil(); }\n")
    manifest, reason = viewer_mod.load_vendor(tmp_path)
    assert manifest is None and "does not match" in reason


def test_load_vendor_rejects_a_manifest_for_another_lock(tmp_path):
    make_fake_vendor(tmp_path)
    doc = json.loads((tmp_path / "manifest.json").read_text())
    doc["lock_sha256"] = "0" * 64
    (tmp_path / "manifest.json").write_text(json.dumps(doc))
    manifest, reason = viewer_mod.load_vendor(tmp_path)
    assert manifest is None and "different vendor/cesium.lock" in reason


@pytest.mark.parametrize("accept, encoding", [("br, gzip", "br"), ("gzip", "gzip"), ("", None)])
def test_vendor_route_serves_precompressed_with_immutable_caching(vendor_client, vendor, accept, encoding):
    rel = "cesium-1.147.0/index.js"
    resp = vendor_client.get(f"/static/vendor/{rel}", headers={"Accept-Encoding": accept})
    assert resp.status_code == 200
    assert resp.headers.get("Content-Encoding") == encoding
    assert resp.mimetype == "text/javascript"
    assert resp.headers["Cache-Control"] == "public, max-age=31536000, immutable"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    info = vendor["files"][rel] if encoding is None else vendor["files"][rel]["encodings"][encoding]
    assert hashlib.sha256(resp.data).hexdigest() == info["sha256"]
    assert resp.headers["ETag"] == f'"{info["sha256"]}"'
    again = vendor_client.get(f"/static/vendor/{rel}", headers={"Accept-Encoding": accept,
                                                                 "If-None-Match": resp.headers["ETag"]})
    assert again.status_code == 304


def test_vendor_route_serves_only_manifest_files(vendor_client):
    assert vendor_client.get("/static/vendor/manifest.json").status_code == 404
    assert vendor_client.get("/static/vendor/cesium-1.147.0/index.js.br").status_code == 404
    assert vendor_client.get("/static/vendor/../vendor/cesium.lock").status_code == 404
    jpg = vendor_client.get("/static/vendor/cesium-1.147.0/Assets/Textures/NaturalEarthII/0/0/0.jpg")
    assert jpg.status_code == 200 and jpg.mimetype == "image/jpeg" and "Content-Encoding" not in jpg.headers


def test_viewer_static_files_exist():
    for name in ("viewer.js", "worker.js", "viewer.css"):
        assert (REPO_ROOT / "static" / "viewer" / name).is_file()


def test_viewer_writes_data_strings_with_text_content_only():
    """Every data string reaches the page through textContent (roadmap 3.2): no HTML parsing sinks, no eval, and no
    URL outside the app's own origin in the viewer's code (D-014)."""
    import re
    for name in ("viewer.js", "worker.js"):
        src = (REPO_ROOT / "static" / "viewer" / name).read_text(encoding="utf-8")
        for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
            assert sink not in src, f"{name} uses {sink}"
        code = "\n".join(line for line in src.splitlines() if not line.lstrip().startswith("//"))
        hosts = set(re.findall(r"https?://([^/\"'`\s]+)", code))
        # the only absolute URLs are the credit links' targets (opened by the user, never fetched)
        assert hosts <= {"www.space-track.org", "planet4589.org", "cesium.com", "github.com",
                         "www.naturalearthdata.com"}, hosts
