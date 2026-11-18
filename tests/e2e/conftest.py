"""Browser (E2E) test set-up: start the app on the sample, open it in headless Chromium, fail on browser errors.

Run: uv run --group e2e playwright install chromium   (once)
     uv run --group e2e pytest tests/e2e -q
"""
import base64
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
def base_url(tmp_path_factory):
    """The app on a free local port (tests/e2e/serve.py). Its log goes to a file, not a pipe: an unread pipe
    fills up and blocks the server."""
    port = _free_port()
    log_path = tmp_path_factory.mktemp("e2e") / "app.log"
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen([sys.executable, str(REPO_ROOT / "tests" / "e2e" / "serve.py"), str(port)],
                                cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT)
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
    pg = context.new_page()
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
