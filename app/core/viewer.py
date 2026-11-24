"""The Cesium viewer's server side (roadmap 3.2; decisions D-013, D-014; proposed D-038).

- Feature flag: SATTRACK_CESIUM_VIEWER=1 turns the viewer on. Off by default, so production is unchanged: with it off
  the tracker page has no globe tab, no viewer stores or clientside callback, and no new headers.
- Self-hosted packages: vendor/fetch.py (run by the Heroku build's bin/post_compile hook) extracts the files pinned in
  vendor/cesium.lock into static/vendor/ with a manifest. At start-up the app checks the manifest against the lock and
  every file against its SHA-256; GET /static/vendor/<path> serves only files in the manifest, pre-compressed
  (Brotli or gzip, as for the data files), with year-long immutable caching (the folders are versioned). If the files
  are missing or don't verify, the viewer stays off and the log says why: the page falls back to the Plotly views.
- Security headers (flag on only, proposed D-038): a report-only Content-Security-Policy and HSTS.
"""
import base64
import hashlib
import json
import os
import re
from pathlib import Path

from flask import Response, abort, request, send_file
from werkzeug.http import parse_etags

from app.core.data_files import choose_encoding

REPO_ROOT = Path(__file__).resolve().parents[2]
FLAG_ENV = "SATTRACK_CESIUM_VIEWER"
VENDOR_DIR_ENV = "SATTRACK_VENDOR_DIR"   # tests and local experiments only; production uses static/vendor
LOCK_PATH = REPO_ROOT / "vendor" / "cesium.lock"
VIEWER_DIR = REPO_ROOT / "static" / "viewer"
VENDOR_URL = "/static/vendor/"
SUFFIX = {"br": ".br", "gzip": ".gz"}
MIMETYPES = {".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".md": "text/markdown",
             ".jpg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml"}
IMMUTABLE = "public, max-age=31536000, immutable"

# HSTS (proposed D-038): a short max-age first, raised once HTTPS on every host name is confirmed; no
# includeSubDomains or preload, which are hard to undo.
HSTS = "max-age=86400"

# Third parties the existing page shell loads (run_app.py index_string, dbc.themes.CYBORG, the Plotly 2D map tiles).
# Listed so the report-only policy reports only new problems; removing them is proposed in D-038, and the Plotly
# entries go with the Plotly views in roadmap 3.6. The viewer itself needs none of them.
SHELL_THIRD_PARTIES = {
    "script-src": ["https://www.googletagmanager.com"],
    "style-src": ["https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"],
    "font-src": ["https://cdnjs.cloudflare.com", "https://fonts.gstatic.com"],
    "img-src": ["https://www.googletagmanager.com", "https://*.google-analytics.com", "https://basemap.nationalmap.gov"],
    "connect-src": ["https://www.googletagmanager.com", "https://*.google-analytics.com",
                    "https://*.analytics.google.com", "https://basemap.nationalmap.gov"],
}


def flag_on(environ=os.environ):
    return environ.get(FLAG_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def vendor_dir(environ=os.environ):
    return Path(environ.get(VENDOR_DIR_ENV) or REPO_ROOT / "static" / "vendor")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_vendor(directory=None, lock_path=LOCK_PATH):
    """The verified vendor manifest, or (None, reason). Checks the manifest was written for the committed lock and
    that every file (and pre-compressed copy) matches its SHA-256."""
    directory = Path(directory or vendor_dir())
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"no readable {directory / 'manifest.json'} ({type(e).__name__}): run python vendor/fetch.py"
    if manifest.get("lock_sha256") != hashlib.sha256(Path(lock_path).read_bytes()).hexdigest():
        return None, "static/vendor was built from a different vendor/cesium.lock: run python vendor/fetch.py"
    for rel, entry in manifest.get("files", {}).items():
        for enc, info in [("identity", entry)] + list(entry.get("encodings", {}).items()):
            path = directory / (rel + SUFFIX.get(enc, ""))
            try:
                if _sha256(path) != info["sha256"]:
                    return None, f"{rel} ({enc}) does not match the manifest"
            except OSError:
                return None, f"{rel} ({enc}) is missing"
    manifest["dir"] = str(directory)
    return manifest, None


def viewer_config(manifest):
    """What the browser needs (the viewer-config store): same-origin URLs only. Viewer files carry a content hash so
    a deploy is picked up at once; vendor folders are versioned."""
    dest = {p["name"]: p["dest"] for p in manifest["packages"]}

    def own(name):
        return f"/static/viewer/{name}?v={_sha256(VIEWER_DIR / name)[:12]}"

    return {"module": own("viewer.js"), "worker": own("worker.js"), "css": own("viewer.css"),
            "cesium": f"{VENDOR_URL}{dest['cesium']}/", "satellite": f"{VENDOR_URL}{dest['satellite.js']}/",
            "data": "/data/objects.json"}


_STATE = {"checked": False, "manifest": None, "reason": None}


def viewer_state():
    """{'enabled': bool, 'manifest': ..., 'reason': ...}, worked out once per process and logged. With the flag off
    the vendor files aren't read or hashed at all, so production pays nothing at boot until the globe is switched on."""
    if not _STATE["checked"]:
        _STATE["checked"] = True
        manifest, reason = load_vendor() if flag_on() else (None, "the viewer flag is off")
        _STATE["manifest"], _STATE["reason"] = manifest, reason
        if flag_on():
            if manifest:
                print(f" - Cesium viewer: on ({len(manifest['files'])} vendor files verified)")
            else:
                print(f" - Cesium viewer: WARNING flag on but disabled: {reason}")
    return {"enabled": flag_on() and _STATE["manifest"] is not None, "manifest": _STATE["manifest"],
            "reason": _STATE["reason"]}


def viewer_enabled():
    return viewer_state()["enabled"]


def reset_viewer_state():
    _STATE.update(checked=False, manifest=None, reason=None)


# ---- GET /static/vendor/<path> ----------------------------------------------------------------------------------

def vendor_response(manifest, rel, accept_encoding, if_none_match):
    entry = manifest["files"].get(rel) if manifest else None
    if entry is None:
        return None
    enc = choose_encoding(accept_encoding, entry.get("encodings", {})) or "identity"
    info = entry if enc == "identity" else entry["encodings"][enc]
    headers = {"Cache-Control": IMMUTABLE, "ETag": f'"{info["sha256"]}"', "X-Content-Type-Options": "nosniff"}
    if entry.get("encodings"):
        headers["Vary"] = "Accept-Encoding"
    if if_none_match and parse_etags(if_none_match).contains_weak(info["sha256"]):
        return Response(status=304, headers=headers)
    path = Path(manifest["dir"]) / (rel + SUFFIX.get(enc, ""))
    resp = send_file(path, mimetype=MIMETYPES.get(Path(rel).suffix, "application/octet-stream"),
                     conditional=False, etag=False, max_age=None)
    resp.headers.update(headers)
    if enc != "identity":
        resp.headers["Content-Encoding"] = enc   # also tells flask-compress to leave it alone
    return resp


def register_vendor_routes(server):
    """GET /static/vendor/<path>: more specific than Flask's /static/<path>, so it takes these URLs."""

    @server.route(VENDOR_URL + "<path:rel>")
    def serve_vendor(rel):
        response = vendor_response(viewer_state()["manifest"], rel, request.headers.get("Accept-Encoding"),
                                   request.headers.get("If-None-Match"))
        if response is None:
            abort(404)
        return response


# ---- Security headers (flag on) ----------------------------------------------------------------------------------

def inline_script_hashes(app):
    """CSP hashes of every inline script the page carries: Dash's own (renderer, clientside callbacks) and those in
    app.index_string (the analytics snippet)."""
    hashes = set(app.csp_hashes())
    for body in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", app.index_string, flags=re.S):
        if body.strip():
            hashes.add("'sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode() + "'")
    return sorted(hashes)


def content_security_policy(app):
    """The report-only policy (D-041): same origin for everything the viewer uses ('self', worker-src 'self'), plus
    'wasm-unsafe-eval' for the small WebAssembly modules Cesium compiles at load (and satellite.js's WASM engine in
    roadmap 3.11), and no 'unsafe-eval' (vendor/cesium.lock patches Cesium's one eval). Plus the page shell's existing
    third parties (SHELL_THIRD_PARTIES). Enforced at roadmap 3.6, once Plotly's blob: workers are gone. Styles allow 'unsafe-inline' because Dash components and Plotly write style
    attributes and <style> elements."""
    third = SHELL_THIRD_PARTIES
    directives = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'wasm-unsafe-eval'", "'report-sample'"] + inline_script_hashes(app)
        + third["script-src"],
        "style-src": ["'self'", "'unsafe-inline'"] + third["style-src"],
        "img-src": ["'self'", "data:", "blob:"] + third["img-src"],
        "font-src": ["'self'", "data:"] + third["font-src"],
        "connect-src": ["'self'"] + third["connect-src"],
        "worker-src": ["'self'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "frame-ancestors": ["'self'"],
    }
    return "; ".join(f"{k} {' '.join(v)}" for k, v in directives.items())


def register_security_headers(app):
    """With the viewer on: Content-Security-Policy-Report-Only and HSTS on every response (proposed D-038)."""
    policy = content_security_policy(app)

    @app.server.after_request
    def add_security_headers(response):
        response.headers.setdefault("Content-Security-Policy-Report-Only", policy)
        response.headers.setdefault("Strict-Transport-Security", HSTS)
        return response

    return policy


def register_viewer(app):
    """Call after every callback is registered (the CSP hashes include clientside callbacks)."""
    register_vendor_routes(app.server)
    if viewer_enabled():
        register_security_headers(app)
