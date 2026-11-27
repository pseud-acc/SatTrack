"""Browser (E2E) test set-up: start the app on the sample, open it in headless Chromium, fail on browser errors.

Run: uv run --group e2e playwright install chromium   (once)
     uv run --group e2e pytest tests/e2e -q
"""
import base64
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # the repo root: app.core.viewer's host list
from _support import load_sample, reference_time  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL = "http://127.0.0.1"
# Software WebGL: Plotly's 3D view and the 2D map need WebGL, and CI runners have no GPU.
CHROMIUM_ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
# Console messages caused by the blocked third-party requests (below). Requests to the app itself are checked
# separately (requestfailed / HTTP status), so ignoring these can't hide a failure of the app.
BLOCKED_REQUEST_MESSAGES = ("Failed to load resource", "Failed to fetch")
BLANK_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url(tmp_path_factory, vendor_dir):
    """The app as production runs it: the globe on (the default since D-052) with the real vendor files."""
    env = {k: v for k, v in os.environ.items() if k != "SATTRACK_CESIUM_VIEWER"}
    env["SATTRACK_VENDOR_DIR"] = str(vendor_dir)
    yield from _serve(tmp_path_factory, env)


@pytest.fixture(scope="session")
def vendor_dir():
    """The real self-hosted Cesium and satellite.js, fetched and verified by vendor/fetch.py (D-014) into
    SATTRACK_VENDOR_DIR if set (e.g. outside a synced folder), else static/vendor. Downloads only when the folder
    doesn't match vendor/cesium.lock; SATTRACK_VENDOR_CACHE keeps the tarballs between runs."""
    out = Path(os.environ.get("SATTRACK_VENDOR_DIR") or REPO_ROOT / "static" / "vendor")
    cmd = [sys.executable, str(REPO_ROOT / "vendor" / "fetch.py"), "--out", str(out)]
    if os.environ.get("SATTRACK_VENDOR_CACHE"):
        cmd += ["--cache", os.environ["SATTRACK_VENDOR_CACHE"]]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT, timeout=600)
    return out


@pytest.fixture(scope="session")
def viewer_url(base_url):
    """The globe's tests run against production's set-up (D-052: the globe is on by default), on the same server."""
    return base_url


@pytest.fixture(scope="session")
def budget_data(tmp_path_factory):
    """A copy of the sample's files with objects.json.br/.gz replaced by a full-size synthetic catalogue
    (tests/e2e/test_viewer.py synthetic_catalogue). The same folder serves this branch and the baseline, so the
    start-up comparison measures the code, not the data."""
    import brotli
    import gzip
    import shutil

    from test_viewer import synthetic_catalogue
    data_dir = tmp_path_factory.mktemp("budget-data")
    for f in (REPO_ROOT / "tests" / "app_data").iterdir():
        if f.is_file():
            shutil.copy(f, data_dir / f.name)
    body = synthetic_catalogue()
    (data_dir / "objects.json.br").write_bytes(brotli.compress(body, quality=5))
    (data_dir / "objects.json.gz").write_bytes(gzip.compress(body, 6))
    return data_dir


@pytest.fixture(scope="session")
def budget_url(tmp_path_factory, vendor_dir, budget_data):
    """The viewer app serving the full-size catalogue, for the D-027 budget and the D-042 start-up checks."""
    env = dict(os.environ, SATTRACK_CESIUM_VIEWER="1", SATTRACK_VENDOR_DIR=str(vendor_dir),
               SATTRACK_E2E_DATA_DIR=str(budget_data))
    yield from _serve(tmp_path_factory, env)


@pytest.fixture(scope="session")
def baseline_url(tmp_path_factory, budget_data):
    """The baseline for the start-up comparison (D-042): the target branch, checked out by CI into
    SATTRACK_BASELINE_DIR, serving the same full-size catalogue with its own pinned vendor files. None when the
    variable isn't set or the baseline has no viewer yet (e.g. main before roadmap 3.2)."""
    root = os.environ.get("SATTRACK_BASELINE_DIR")
    if not root:
        yield None
        return
    root = Path(root).resolve()
    if not ((root / "vendor" / "fetch.py").is_file() and (root / "tests" / "e2e" / "serve.py").is_file()):
        yield None
        return
    out = tmp_path_factory.mktemp("baseline-vendor")
    cmd = [sys.executable, str(root / "vendor" / "fetch.py"), "--out", str(out)]
    if os.environ.get("SATTRACK_VENDOR_CACHE"):
        cmd += ["--cache", os.environ["SATTRACK_VENDOR_CACHE"]]
    subprocess.run(cmd, check=True, cwd=root, timeout=600)
    env = dict(os.environ, SATTRACK_CESIUM_VIEWER="1", SATTRACK_VENDOR_DIR=str(out),
               SATTRACK_E2E_DATA_DIR=str(budget_data))
    yield from _serve(tmp_path_factory, env, root=root)


def _serve(tmp_path_factory, env, root=REPO_ROOT):
    """The app on a free local port (tests/e2e/serve.py of `root`: this checkout, or the baseline's). Its log goes
    to a file, not a pipe: an unread pipe fills up and blocks the server."""
    port = _free_port()
    log_path = tmp_path_factory.mktemp("e2e") / "app.log"
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen([sys.executable, str(root / "tests" / "e2e" / "serve.py"), str(port)],
                                cwd=root, stdout=log, stderr=subprocess.STDOUT, env=env)
        url = f"{LOCAL}:{port}"
        deadline = time.time() + 120
        while True:
            if proc.poll() is not None:
                raise RuntimeError("app exited:\n" + log_path.read_text(errors="replace")[-3000:])
            try:
                urllib.request.urlopen(url + "/_dash-layout", timeout=2)
                break
            except OSError:
                if time.time() > deadline:
                    proc.kill()
                    raise RuntimeError("app did not start within 120 s")
                time.sleep(0.5)
        yield url
        proc.terminate()
        proc.wait(timeout=10)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(args=CHROMIUM_ARGS)
        yield b
        b.close()


CSP_RECORDER = """
window.__cspViolations = [];
document.addEventListener("securitypolicyviolation", (e) => window.__cspViolations.push(
    {directive: e.violatedDirective, blocked: e.blockedURI, source: e.sourceFile, sample: e.sample}));
"""
MAP_TILE = re.compile(r"/tile/\d+/\d+/\d+$")   # the 2D map's raster layer: .../MapServer/tile/{z}/{y}/{x}


def _offline(route):
    """Third-party requests: map tiles get a blank 1x1 PNG, because Mapbox throws an uncaught error on a failed
    tile; everything else (analytics, CDN stylesheets, fonts) is refused."""
    if MAP_TILE.search(route.request.url):
        route.fulfill(status=200, content_type="image/png", body=BLANK_PNG)
    else:
        route.abort()


def _console_error(pg, msg):
    if msg.type == "error" and not any(m in msg.text for m in BLOCKED_REQUEST_MESSAGES):
        pg.errors.append(f"console: {msg.text}")


@pytest.fixture
def page(browser):
    """A desktop-size page that records uncaught JS errors, console errors and failed or 4xx/5xx requests to
    the app. Requests to anything but the local app (analytics, icon fonts, map styles and tiles) are blocked,
    so the tests never depend on the internet and never send analytics hits."""
    context = browser.new_context(viewport={"width": 1366, "height": 900})
    context.route(re.compile(r"^(?!http://127\.0\.0\.1[:/]).*"), _offline)
    # Also kept for the viewer tests: every off-site request (from the page or its workers) and every CSP violation
    # the page reports (window.__cspViolations; the policy is report-only, so nothing is blocked).
    context.add_init_script(CSP_RECORDER)
    pg = context.new_page()
    pg.offsite = []
    context.on("request", lambda req: req.url.startswith(("http:", "https:")) and not req.url.startswith(LOCAL)
               and pg.offsite.append(req.url))
    pg.errors = []
    pg.on("pageerror", lambda exc: pg.errors.append(f"JS error: {exc}"))
    pg.on("console", lambda msg: _console_error(pg, msg))
    pg.on("requestfailed", lambda req: req.url.startswith(LOCAL) and pg.errors.append(f"request failed: {req.url}"))
    pg.on("response", lambda resp: resp.url.startswith(LOCAL) and resp.status >= 400
          and pg.errors.append(f"HTTP {resp.status}: {resp.url}"))
    yield pg
    context.close()


@pytest.fixture(scope="session")
def sample_df():
    return load_sample()


@pytest.fixture(scope="session")
def t_ref():
    return reference_time()
