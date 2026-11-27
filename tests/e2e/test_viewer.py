"""E2E: the Cesium viewer (roadmap 3.2) with SATTRACK_CESIUM_VIEWER on, the real self-hosted Cesium and
satellite.js (vendor/fetch.py) and the sample objects dataset, in headless Chromium with software WebGL.

- Journeys: the globe opens with payloads coloured by type, toggles and space junk mode, credits, UNKNOWN hidden,
  the globe survives tab switches, and the clock follows the server's Date header.
- Parity: positions from the browser's worker against the Python sgp4 library (independent code), 50 m tolerance,
  both sides failing on the same objects.
- Budget (D-027): main-thread ms per frame, time to first positions and heap, on a full-size synthetic catalogue.
  CI has no GPU, so frame rates are a release check on the reference laptop, not here.
- Start-up (D-042): fixed budgets that don't depend on the runner's speed (bytes downloaded and records built
  before the first positions, heap), and, when CI provides a baseline checkout of the target branch, cold visits
  to both apps interleaved on the same runner, compared phase by phase. Both go to the CI job summary.
- Security: no off-site request from the viewer and no CSP violation beyond the known, recorded ones.

Waits poll from Python (page.evaluate) rather than page.wait_for_function, which evaluates a string in the page and
would itself be reported by the CSP.
"""
import gzip
import json
import math
import re
import os
import statistics
import time
import warnings
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import expect

from app.core.viewer import SHELL_THIRD_PARTIES

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE = REPO_ROOT / "tests" / "app_data" / "objects.json.gz"
TIMEOUT_S = 90
PARITY_KM = 0.050   # 50 m (roadmap 3.2); the spike measured 9.5 m at most
# Start-up checks (D-042). D-027's 1.5 s for first positions is a laptop budget: GitHub's runners render the globe in
# software (SwiftShader) on the CPUs the propagation worker needs and measured 1.40-1.98 s where the laptop measured
# 0.84-1.22 s. So CI's timing check is relative (this branch against the baseline, same runner, interleaved), with
# an absolute ceiling as a backstop, and the 1.5 s stays the release check on the reference laptop.
FIRST_POSITIONS_CEILING_MS = 3000        # backstop, and the only timing limit when there's no baseline
REGRESSION_LIMIT = 1.20                  # a phase fails if its median is over 20% slower than the baseline's ...
REGRESSION_FLOOR_MS = 150                # ... and over 150 ms slower (smaller phases are noise on a shared runner)
STARTUP_VISITS = 3                       # cold visits per app; the median is compared
# Fixed budgets: the same on any machine. Bytes are as sent (Brotli), from the first request to the first positions.
BYTES_BEFORE_FIRST_POSITIONS_MB = 5.0     # measured 3.95-4.03 MB on 24 Nov 2026
HEAP_MB = 80
PHASES = (("data", "Data fetched + parsed"), ("cesium", "Cesium loaded"), ("viewer", "Globe created"),
          ("ready", "Records built + first samples"), ("firstPositions", "First positions"))
LONG_TASKS = """
window.__longTasks = [];
try {
  new PerformanceObserver((list) => { for (const e of list.getEntries()) window.__longTasks.push([e.startTime, e.duration]); })
    .observe({ type: "longtask", buffered: true });
} catch (e) {}
"""

# CSP reports that are known and recorded, by (directive, blocked, path of the reporting script). Anything else fails.
# Cesium reports nothing: its WebAssembly is allowed ('wasm-unsafe-eval') and its one eval is patched at vendoring
# (D-041). Left: Plotly's 2D map starts its workers from blob: URLs, which goes with the Plotly views in roadmap 3.6,
# when the policy is enforced.
KNOWN_CSP = {
    ("worker-src", "blob", "/_dash-component-suites/plotly/package_data/plotly.min.js"),
}
SHELL_HOSTS = {u.split("://", 1)[1].removeprefix("*.") for urls in SHELL_THIRD_PARTIES.values() for u in urls}


class Measurement(UserWarning):
    """Parity and budget figures, shown in pytest's warnings summary so CI logs carry them on a passing run."""


def report(message):
    print(message)
    warnings.warn(message.strip(), Measurement, stacklevel=2)


def wait_until(page, expression, timeout_s=TIMEOUT_S):
    deadline = time.time() + timeout_s
    while True:
        value = page.evaluate(expression)
        if value:
            return value
        if time.time() > deadline:
            raise AssertionError(f"timed out waiting for {expression}; viewer error: "
                                 f"{page.evaluate('window.sattrackViewer && window.sattrackViewer.error')}")
        page.wait_for_timeout(250)


def open_viewer(page, url):
    page.goto(url + "/sat_visualisation", wait_until="domcontentloaded")
    wait_until(page, "() => !!(window.sattrackViewer && (window.sattrackViewer.ready || window.sattrackViewer.error))")
    assert page.evaluate("window.sattrackViewer.error") is None
    return page.evaluate("window.sattrackViewer.metrics()")


def sample_records():
    return json.loads(gzip.decompress(SAMPLE.read_bytes()))


def check_security(page):
    """No off-site request except the page shell's existing third parties (and none to any CDN for the viewer), and
    no CSP violation beyond KNOWN_CSP."""
    for url in page.offsite:
        host = urlparse(url).hostname
        assert any(host == h or host.endswith("." + h) for h in SHELL_HOSTS), f"off-site request: {url}"
    assert not [u for u in page.offsite if "cesium" in u.lower() or "satellite" in u.lower()]
    unknown = []
    for v in page.evaluate("window.__cspViolations"):
        path = urlparse(v["source"] or "").path
        if (v["directive"], v["blocked"], path) not in KNOWN_CSP:
            unknown.append(v)
    assert not unknown, f"CSP violations: {unknown}"


# ---- journeys ---------------------------------------------------------------------------------------------------

ALL_ORBITS = {"LEO", "MEO", "GEO", "GSO", "HEO"}


def expected_shown(records, page, types, statuses):
    """satcat_ids the page's filters should show, worked out here in plain Python over the sample (not with the app's
    filter code): the given types and statuses, any orbit class, a launch year inside the slider's range (objects with
    no year are outside it), never UNKNOWN; minus the objects satellite.js can't place."""
    year = page.evaluate("window.sattrackViewerBridge.filters.clauses.find(c => c.field === 'launch_year').value")
    lo, hi = year["min"], year["max"]
    shown = {r["satcat_id"] for r in records
             if r["object_type"] in types and r["object_type"] != "UNKNOWN"
             and (r["operational_status"] if r["operational_status"] is not None else "Inactive") in statuses
             and r["orbit_class"] in ALL_ORBITS
             and r["launch_year"] is not None and lo <= r["launch_year"] <= hi}
    return shown - set(page.evaluate("window.sattrackViewer.failed"))


def shown_ids(page):
    return set(page.evaluate("window.sattrackViewer.shownIds()"))


def objects_requests(page):
    return page.evaluate("performance.getEntriesByType('resource').filter(e => e.name.includes('/data/objects.json'))"
                         ".length")


def test_globe_opens_with_active_payloads_coloured_by_status(page, viewer_url):
    """The page's starting spec (every active payload, any orbit; owner 26 Nov 2026) masks the globe before its first
    positions; points take the status tokens and have no outline (owner, 24 Nov 2026)."""
    m = open_viewer(page, viewer_url)
    records = sample_records()["records"]
    assert m["engine"] == "worker-js" and m["count"] == len(records)
    expect(page.locator("#sat-viz-tabs .nav-link.active")).to_have_text("Globe")
    wait_until(page, "() => window.sattrackViewer.shownCount > 0")
    want = expected_shown(records, page, {"PAYLOAD"}, {"Active"})
    assert len(want) > 0 and shown_ids(page) == want
    assert page.evaluate("window.sattrackViewer.colours") == {"active": "#e8564a", "inactive": "#7d8aa0"}
    assert page.locator(".sattrack-viewer-legend, .sattrack-viewer-panel input").count() == 0   # toggles: panel
    expect(page.locator("#globe canvas").first).to_be_visible()
    assert page.errors == []
    check_security(page)


def test_panel_type_switches_and_space_junk_mode_filter_the_globe_without_reloading(page, viewer_url):
    """Roadmap 3.3a: the panel's controls drive the globe through the filter spec. Debris on its own shows nothing
    while status is Active (the sample's debris are all Inactive; the note says they always are); junk mode adds rocket bodies, debris and
    Inactive; off restores. The data is fetched once and the canvas and worker survive every change."""
    open_viewer(page, viewer_url)
    records = sample_records()["records"]
    page.evaluate("window.__canvas = document.querySelector('#globe canvas')")
    types = page.locator("#type-filter-checkbox")
    expect(page.locator(".st-type-note")).to_contain_text("Rocket bodies and debris are always inactive")
    changes = page.evaluate("window.sattrackViewer.filterChanges")

    types.get_by_text("Debris", exact=True).click()
    wait_until(page, f"() => window.sattrackViewer.filterChanges > {changes}")
    assert page.evaluate("window.sattrackViewer.matchCounts.DEBRIS") == 0
    assert shown_ids(page) == expected_shown(records, page, {"PAYLOAD"}, {"Active"})

    junk = page.get_by_label("Space junk mode")
    junk.check()
    expect(page.locator("#status-filter-checkbox").get_by_label("All", exact=True)).to_be_checked()
    want = expected_shown(records, page, {"PAYLOAD", "ROCKET BODY", "DEBRIS"}, {"Active", "Inactive"})
    wait_until(page, f"() => window.sattrackViewer.shownIds().length === {len(want)}")
    assert shown_ids(page) == want
    assert page.evaluate("window.sattrackViewer.matchCounts.DEBRIS") > 0

    junk.uncheck()
    expect(page.locator("#status-filter-checkbox").get_by_label("Active", exact=True)).to_be_checked()
    want = expected_shown(records, page, {"PAYLOAD"}, {"Active"})
    wait_until(page, f"() => window.sattrackViewer.shownIds().length === {len(want)}")
    assert shown_ids(page) == want

    page.locator("#orbit-filter-checkbox").get_by_text("LEO", exact=True).click()   # a segment: click it
    no_leo = {r["satcat_id"] for r in records if r["orbit_class"] == "LEO"}
    want = expected_shown(records, page, {"PAYLOAD"}, {"Active"}) - no_leo
    wait_until(page, f"() => window.sattrackViewer.shownIds().length === {len(want)}")
    assert shown_ids(page) == want

    assert objects_requests(page) == 1                                     # no data reload
    assert page.evaluate("document.querySelector('#globe canvas') === window.__canvas")
    assert not page.evaluate("window.sattrackViewer.error")
    assert page.errors == []
    check_security(page)


def panel_count(page):
    return int(page.locator("#filter-count .st-count-n").inner_text().replace(",", ""))


def browser_count(page):
    return sum(page.evaluate("window.sattrackViewer.matchCounts").values())


def wait_for_filter(page, changes):
    """Until the viewer has applied the next filter change (newly shown objects placed)."""
    wait_until(page, f"() => window.sattrackViewer.filterChanges > {changes}")
    return page.evaluate("window.sattrackViewer.filterChanges")


def test_panel_count_chips_and_clear_all_drive_the_globe(page, viewer_url):
    """Roadmap 3.3b: the server's count (the panel) equals the browser's match count after each change; the status and
    orbit segments, a chip's remove button and Clear all change the globe at once, with no Update button and no data
    reload."""
    open_viewer(page, viewer_url)
    records = sample_records()["records"]
    wait_until(page, "() => window.sattrackViewer.shownCount > 0")
    assert panel_count(page) == browser_count(page) > 0                       # server count == browser count (Q4)
    assert shown_ids(page) == expected_shown(records, page, {"PAYLOAD"}, {"Active"})
    expect(page.locator("#filter-count")).to_contain_text(f"of {len(records):,} objects")
    assert page.locator("#time-update-btn").count() == 0                     # changes apply at once
    expect(page.locator("#filter-clear-all")).to_be_hidden()
    changes = page.evaluate("window.sattrackViewer.filterChanges")

    page.locator("#status-filter-checkbox").get_by_text("All", exact=True).click()
    changes = wait_for_filter(page, changes)
    want = expected_shown(records, page, {"PAYLOAD"}, {"Active", "Inactive"})
    assert shown_ids(page) == want
    expect(page.locator("#filter-count .st-count-n")).to_have_text(f"{browser_count(page):,}")
    expect(page.locator("#chip-status")).to_be_hidden()                      # All narrows nothing
    expect(page.locator("#filter-clear-all")).to_be_visible()

    page.locator("#orbit-filter-checkbox").get_by_text("LEO", exact=True).click()
    changes = wait_for_filter(page, changes)
    expect(page.locator("#chip-orbit")).to_contain_text("Orbit type: MEO, GEO, GSO, HEO")
    leo = {r["satcat_id"] for r in records if r["orbit_class"] == "LEO"}
    assert shown_ids(page) == want - leo
    expect(page.locator("#filter-count .st-count-n")).to_have_text(f"{browser_count(page):,}")

    page.locator("#chip-x-orbit").click()                                    # remove the orbit chip: every orbit
    changes = wait_for_filter(page, changes)
    expect(page.locator("#orbit-filter-checkbox").get_by_label("LEO", exact=True)).to_be_checked()
    expect(page.locator("#chip-orbit")).to_be_hidden()
    assert shown_ids(page) == want

    page.locator("#filter-clear-all").click()                                # back to the opening values
    wait_for_filter(page, changes)
    expect(page.locator("#status-filter-checkbox").get_by_label("Active", exact=True)).to_be_checked()
    expect(page.locator("#filter-clear-all")).to_be_hidden()
    assert shown_ids(page) == expected_shown(records, page, {"PAYLOAD"}, {"Active"})
    expect(page.locator("#filter-count .st-count-n")).to_have_text(f"{browser_count(page):,}")

    assert objects_requests(page) == 1
    assert page.errors == []
    check_security(page)


def test_more_filters_rows_show_their_values(page, viewer_url):
    open_viewer(page, viewer_url)
    row = page.locator("#more-owner")
    expect(page.locator("#more-owner-summary")).to_have_text("Any")
    expect(page.locator("#owner-filter-multi-dropdown")).to_be_hidden()      # closed until opened
    row.locator("summary").click()
    expect(page.locator("#owner-filter-multi-dropdown")).to_be_visible()
    row.locator("summary").press("Enter")                                    # keyboard closes it again
    expect(page.locator("#owner-filter-multi-dropdown")).to_be_hidden()
    assert page.errors == []


def test_credits_replace_cesiums(page, viewer_url):
    open_viewer(page, viewer_url)
    credits = page.locator(".sattrack-viewer-credits")
    for text in ("USSPACECOM via Space-Track.org", "must not be used for conjunction", "GCAT (J. McDowell",
                 "CC-BY", "CesiumJS", "Apache-2.0", "satellite.js", "MIT", "Natural Earth"):
        expect(credits).to_contain_text(text)
    assert page.locator("#globe .cesium-credit-logoContainer, #globe .cesium-widget-credits").count() == 0
    assert page.errors == []


def test_globe_survives_tab_switches_and_page_changes(page, viewer_url):
    open_viewer(page, viewer_url)
    page.evaluate("window.__firstCanvas = document.querySelector('#globe canvas')")
    page.get_by_role("tab", name="List View").click()
    page.get_by_role("tab", name="Globe", exact=True).click()
    assert page.evaluate("document.querySelector('#globe canvas') === window.__firstCanvas")
    frames = page.evaluate("window.sattrackViewer.frameMs.length")
    wait_until(page, f"() => window.sattrackViewer.frameMs.length > {frames}")
    # leaving the tracker and coming back mounts a fresh viewer in the new div#globe. Wait for the page's requests to
    # finish first: a request the test cancels by navigating away (a globe tile, a callback) isn't an app error.
    page.wait_for_load_state("networkidle")
    page.locator("#nav-home, a[href='/']").first.click()
    page.locator("#nav-viz, a[href='/sat_visualisation']").first.click()
    wait_until(page, "() => !!document.querySelector('#globe canvas') && "
                     "document.querySelector('#globe canvas') !== window.__firstCanvas && window.sattrackViewer.ready")
    assert page.errors == []


def test_clock_follows_the_server_date_header(page, viewer_url):
    """A device clock an hour fast: the viewer corrects it from the server's Date header."""
    page.context.add_init_script("""(() => { const real = Date.now.bind(Date), RealDate = Date;
        Date.now = () => real() + 3600e3;
        window.Date = class extends RealDate { constructor(...a) { super(...(a.length ? a : [real() + 3600e3])); } };
        window.Date.now = Date.now; window.Date.parse = RealDate.parse; window.Date.UTC = RealDate.UTC; })();""")
    m = open_viewer(page, viewer_url)
    assert abs(m["clockOffsetMs"] + 3600e3) < 3000
    shown = page.evaluate("Date.parse(document.querySelector('.sattrack-viewer-status').textContent"
                          ".split('· ')[1].replace(' UTC', 'Z').replace(' ', 'T'))")
    assert abs(shown - time.time() * 1000) < 10_000


# ---- parity with the Python sgp4 library -------------------------------------------------------------------------

def python_positions(records, when):
    """Earth-fixed positions (km) from the sgp4 library directly: OMM fields, then TEME rotated by GMST (the
    rotation satellite.js's eciToEcf applies). Independent of the app and of the browser code."""
    from datetime import datetime, timezone

    from sgp4 import omm
    from sgp4.api import Satrec, jday
    from sgp4.propagation import gstime

    t = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(timezone.utc)
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
    g = gstime(jd + fr)
    out, failed = {}, set()
    for r in records:
        fields = {k.upper(): r[k] for k in ("object_name", "object_id", "epoch", "mean_motion", "eccentricity",
                                             "inclination", "ra_of_asc_node", "arg_of_pericenter", "mean_anomaly",
                                             "ephemeris_type", "classification_type", "element_set_no",
                                             "rev_at_epoch", "bstar", "mean_motion_dot", "mean_motion_ddot")}
        fields["NORAD_CAT_ID"] = r["satcat_id"]
        sat = Satrec()
        try:
            omm.initialize(sat, {k: str(v) for k, v in fields.items()})
            e, p, _ = sat.sgp4(jd, fr)
        except Exception:   # noqa: BLE001 - an object the library can't initialise counts as failed
            e = -1
        if e:
            failed.add(r["satcat_id"])
            continue
        c, s = math.cos(g), math.sin(g)
        out[r["satcat_id"]] = (p[0] * c + p[1] * s, -p[0] * s + p[1] * c, p[2])
    return out, failed


def with_failing_objects(doc):
    """The sample plus element sets SGP4 must reject, so 'both sides fail on the same objects' is tested even though
    every sample object propagates: eccentricity >= 1 (error 1) and an orbit decayed below the surface (error 6)."""
    base = next(r for r in doc["records"] if r["object_type"] == "PAYLOAD" and r["mean_motion"] > 14)
    bad = [{**base, "satcat_id": 999_001, "eccentricity": 1.2},
           {**base, "satcat_id": 999_002, "mean_motion": 17.5, "eccentricity": 0.0, "bstar": 0.5,
            "mean_motion_dot": 0.5}]
    return {**doc, "records": doc["records"] + bad, "count": doc["count"] + len(bad)}


@pytest.mark.parametrize("offset_days", [0, 30])
def test_parity_with_python_sgp4(page, viewer_url, offset_days):
    """At the dataset's generation time and 30 days later, with two element sets that must fail on both sides."""
    doc = with_failing_objects(sample_records())
    page.context.route("**/data/objects.json", lambda route: route.fulfill(
        status=200, body=json.dumps(doc), headers={"Content-Type": "application/json"}))
    open_viewer(page, viewer_url)
    from datetime import datetime, timedelta
    when = (datetime.fromisoformat(doc["generated_at"].replace("Z", "+00:00")) + timedelta(days=offset_days))
    when = when.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    rows = page.evaluate("iso => window.sattrackViewer.snapshot(iso)", when)
    browser = {r[0]: r[1:] for r in rows}
    py, py_failed = python_positions(doc["records"], when)
    assert set(browser) == {r["satcat_id"] for r in doc["records"]}
    b_failed = {sid for sid, v in browser.items() if not all(x is not None and math.isfinite(x) for x in v)}
    assert b_failed == py_failed, f"browser-only failures {b_failed - py_failed}, python-only {py_failed - b_failed}"
    assert {999_001, 999_002} <= py_failed
    diffs = sorted((math.dist(browser[sid], q), sid) for sid, q in py.items())
    report(f"\nparity at {when}: {len(diffs)} objects, max {diffs[-1][0] * 1000:.2f} m (satcat {diffs[-1][1]}), "
          f"failed on both sides {len(py_failed)}")
    assert diffs[-1][0] <= PARITY_KM


# ---- performance budget (D-027), CI-checkable parts ---------------------------------------------------------------

def synthetic_catalogue(n_payload=19_742, n_rb=2_219, n_debris=10_179, n_unknown=512):
    """A full-size catalogue (the 21 Nov 2026 mix) from the sample's element sets, re-numbered: positions don't
    matter here, only the amount of work."""
    doc = sample_records()
    src = [r for r in doc["records"] if r["object_type"] == "PAYLOAD"]
    records, sid = [], 1
    for obj_type, n in (("PAYLOAD", n_payload), ("ROCKET BODY", n_rb), ("DEBRIS", n_debris), ("UNKNOWN", n_unknown)):
        for i in range(n):
            records.append({**src[i % len(src)], "satcat_id": sid, "object_type": obj_type})
            sid += 1
    doc.update(records=records, count=len(records))
    return json.dumps(doc).encode()


def heap_mb(page):
    cdp = page.context.new_cdp_session(page)
    cdp.send("Performance.enable")
    metrics = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    return metrics["JSHeapUsedSize"] / 1e6


def startup_profile(browser, url):
    """One first visit (a fresh browser context, nothing cached): each load phase in ms after the viewer started,
    the bytes received (as sent, compressed) before the first positions, the records the worker built before them,
    and the main thread's long tasks (> 50 ms) before them."""
    context = browser.new_context(viewport={"width": 1366, "height": 900})
    context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
    context.add_init_script(LONG_TASKS)
    finished = []
    context.on("requestfinished", lambda req: finished.append(req))
    try:
        pg = context.new_page()
        open_viewer(pg, url)
        k = pg.evaluate("window.sattrackViewer.marks")
        first_epoch = pg.evaluate("performance.timeOrigin") + k["firstPositions"]
        received = 0
        for req in finished:
            t = req.timing
            if t["startTime"] + max(t["responseEnd"], 0) <= first_epoch:
                s = req.sizes()
                received += s["responseBodySize"] + s["responseHeadersSize"]
        tasks = [d for (st, d) in pg.evaluate("window.__longTasks || []") if st < k["firstPositions"]]
        return {
            "phases": {name: k[name] - k["start"] for name, _ in PHASES if name in k},
            "bytes": received,
            "built": pg.evaluate("window.sattrackViewer.builtBeforeReady"),
            "long_tasks": len(tasks),
            "longest_task": max(tasks, default=0),
        }
    finally:
        context.close()


def median_profile(profiles):
    """The phases of the visit with the median first positions (an odd number of visits), so the phases shown come
    from one real visit and stay in order, rather than per-phase medians taken from different visits."""
    ranked = sorted(profiles, key=lambda p: p["phases"]["firstPositions"])
    return dict(ranked[len(ranked) // 2]["phases"])


def job_summary(markdown):
    """The CI job summary (GITHUB_STEP_SUMMARY) when there is one, and the pytest warnings summary always."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(markdown + "\n\n")
    report("\n" + markdown)


def test_budget_full_catalogue(page, browser, budget_url):
    """D-027 budget and D-042's fixed start-up budgets, the parts CI can check without a GPU, with payloads (the
    default view) of a full-size catalogue served by the app (Brotli): bytes and records before the first positions,
    first positions under the ceiling (median of 3 first visits), main thread <= 5 ms a frame, heap <= 80 MB. Then
    space junk mode (main thread checked)."""
    profiles = [startup_profile(browser, budget_url) for _ in range(STARTUP_VISITS)]
    med = median_profile(profiles)
    m = open_viewer(page, budget_url)
    assert m["count"] == 32_652
    payloads = 19_742
    page.evaluate("for (const k of ['frameMs', 'applyMs', 'workerMs']) window.sattrackViewer[k].length = 0")
    page.wait_for_timeout(8000)
    m = page.evaluate("window.sattrackViewer.metrics()")
    heap = heap_mb(page)
    mb = statistics.median(p["bytes"] for p in profiles) / 1e6
    built = profiles[0]["built"]
    long_tasks = statistics.median(p["long_tasks"] for p in profiles)
    longest = statistics.median(p["longest_task"] for p in profiles)
    rows = "\n".join(f"| {label} | {med[n]:,.0f} ms |" for n, label in PHASES if n in med)
    ok = lambda good: "ok" if good else "FAIL"  # noqa: E731
    job_summary(
        f"### Viewer start-up: fixed budgets (D-042)\n\n"
        f"Full-size catalogue (32,652 objects, payloads shown), median of {STARTUP_VISITS} first visits.\n\n"
        f"| Check | Value | Limit | |\n|---|---|---|---|\n"
        f"| Bytes before first positions | {mb:.2f} MB | {BYTES_BEFORE_FIRST_POSITIONS_MB} MB | "
        f"{ok(mb <= BYTES_BEFORE_FIRST_POSITIONS_MB)} |\n"
        f"| Records built before first positions | {built:,} | {payloads:,} (payloads only) | {ok(built == payloads)} |\n"
        f"| Heap after load | {heap:.1f} MB | {HEAP_MB} MB | {ok(heap <= HEAP_MB)} |\n"
        f"| Main thread per frame | {m['mainMsPerFrame']:.2f} ms | 5 ms | {ok(m['mainMsPerFrame'] <= 5)} |\n"
        f"| First positions (ceiling) | {med['firstPositions']:,.0f} ms | {FIRST_POSITIONS_CEILING_MS:,} ms | "
        f"{ok(med['firstPositions'] <= FIRST_POSITIONS_CEILING_MS)} |\n"
        f"| Long main-thread tasks before first positions | {long_tasks:.0f} (longest {longest:.0f} ms) | "
        f"reported only | |\n\n"
        f"| Phase (ms after the viewer started, the median visit) | |\n|---|---|\n{rows}")
    report(f"budget, payloads ({m['shown']:,} shown): main {m['mainMsPerFrame']:.2f} ms/frame over {m['frames']} "
           f"frames, worker {m['workerMsPerPass']:.1f} ms/pass, step {m['step']} s, frame {m['frameMs']:.0f} ms "
           f"(software WebGL)")
    assert m["frames"] >= 10
    assert m["mainMsPerFrame"] <= 5
    assert mb <= BYTES_BEFORE_FIRST_POSITIONS_MB
    assert built == payloads, "the worker must build only the shown types' records before the first positions"
    assert med["firstPositions"] <= FIRST_POSITIONS_CEILING_MS
    assert heap <= HEAP_MB
    page.get_by_label("Space junk mode").check()   # the panel's switch (3.3a): all types, Active + Inactive
    wait_until(page, "() => window.sattrackViewer.shownCount > 30000")
    page.evaluate("for (const k of ['frameMs', 'applyMs', 'workerMs']) window.sattrackViewer[k].length = 0")
    page.wait_for_timeout(5000)
    m = page.evaluate("window.sattrackViewer.metrics()")
    report(f"budget, space junk mode ({m['shown']:,} shown): main {m['mainMsPerFrame']:.2f} ms/frame, worker "
          f"{m['workerMsPerPass']:.1f} ms/pass, step {m['step']} s, heap {heap_mb(page):.1f} MB")
    assert m["mainMsPerFrame"] <= 5
    assert page.errors == []


FILTER_MAIN_MS = 50   # the viewer's main-thread work per filter change (D-027: no viewer task over 50 ms)


def test_filter_change_cost(page, budget_url):
    """Roadmap 3.3b: what a filter change costs on a full-size catalogue. For each change: the time from the click to
    the spec reaching the viewer (Dash's round trip: the server builds the spec and the panel summary), then to the
    globe updated (the worker's mask and fresh positions for newly shown objects), the viewer's own main-thread part
    (limited), and the long main-thread tasks (> 50 ms) in the window, reported (Dash's and the renderer's work
    included). The search lists aren't rebuilt (Q8 S2), so a change no longer re-indexes them."""
    page.add_init_script(LONG_TASKS)
    open_viewer(page, budget_url)
    wait_until(page, "() => window.sattrackViewer.shownCount > 0")
    page.wait_for_timeout(1500)
    steps = [
        ("Space junk mode on", lambda: page.get_by_label("Space junk mode").check()),
        ("Status: Active", lambda: page.locator("#status-filter-checkbox").get_by_text("Active", exact=True).click()),
        ("Orbit: LEO off", lambda: page.locator("#orbit-filter-checkbox").get_by_text("LEO", exact=True).click()),
        ("Clear all", lambda: page.locator("#filter-clear-all").click()),
    ]
    rows, worst_main = [], 0.0
    for label, act in steps:
        changes = page.evaluate("window.sattrackViewer.filterChanges")
        t0 = page.evaluate("performance.now()")
        act()
        wait_until(page, f"() => window.sattrackViewer.filterChanges > {changes}")
        received, applied, main_ms, matched = page.evaluate(
            "[window.sattrackViewer.filterReceivedAt, window.sattrackViewer.filterAppliedAt, "
            "window.sattrackViewer.filterMainMs.at(-1), "
            "Object.values(window.sattrackViewer.matchCounts).reduce((a, b) => a + b, 0)]")
        tasks = [d for (st, d) in page.evaluate("window.__longTasks") if t0 <= st <= applied]
        worst_main = max(worst_main, main_ms)
        rows.append(f"| {label} | {matched:,} | {received - t0:,.0f} ms | {applied - received:,.0f} ms | "
                    f"{main_ms:,.1f} ms | {len(tasks)} (longest {max(tasks, default=0):,.0f} ms) |")
    job_summary("### Filter change cost (roadmap 3.3b)\n\nFull-size catalogue (32,652 objects).\n\n"
                "| Change | Matched | Click to spec in the viewer | Then to globe updated | Viewer main thread | "
                "Long tasks (> 50 ms) |\n|---|---|---|---|---|---|\n" + "\n".join(rows)
                + f"\n\nLimit: viewer main thread <= {FILTER_MAIN_MS} ms per change; the rest is reported only.")
    assert worst_main <= FILTER_MAIN_MS
    assert objects_requests(page) == 1
    assert page.errors == []


def test_startup_against_baseline(browser, budget_url, baseline_url):
    """D-042: cold visits to this branch and the baseline (the target branch, same runner, same data), interleaved
    and alternating which goes first, compared phase by phase on the medians. A phase fails if it is over 20% and
    over 150 ms slower than the baseline. Skipped, with a note in the summary, when CI provides no baseline."""
    if baseline_url is None:
        job_summary("### Viewer start-up: against the baseline (D-042)\n\nNo baseline with the viewer "
                    "(SATTRACK_BASELINE_DIR unset, or the target branch predates roadmap 3.2): fixed budgets only.")
        pytest.skip("no baseline with the viewer")
    runs = {"branch": [], "baseline": []}
    for i in range(STARTUP_VISITS):
        pair = [("branch", budget_url), ("baseline", baseline_url)]
        for who, url in (pair if i % 2 == 0 else pair[::-1]):
            runs[who].append(startup_profile(browser, url))
    branch, base = median_profile(runs["branch"]), median_profile(runs["baseline"])
    rows, failed = [], []
    for name, label in PHASES:
        if name not in branch or name not in base:
            continue
        b, p = base[name], branch[name]
        change = (p - b) / b if b else 0
        bad = p > b * REGRESSION_LIMIT and p - b > REGRESSION_FLOOR_MS
        if bad:
            failed.append(label)
        rows.append(f"| {label} | {b:,.0f} ms | {p:,.0f} ms | {change:+.0%} | {'FAIL' if bad else 'ok'} |")
    bb = statistics.median(r["bytes"] for r in runs["baseline"]) / 1e6
    pb = statistics.median(r["bytes"] for r in runs["branch"]) / 1e6
    rows.append(f"| Bytes before first positions | {bb:.2f} MB | {pb:.2f} MB | {(pb - bb) / bb:+.0%} | reported |")
    job_summary(
        f"### Viewer start-up: this branch against the baseline (D-042)\n\n"
        f"Same runner, same full-size catalogue, {STARTUP_VISITS} cold visits each, interleaved; each side's "
        f"median visit (by first positions). A phase "
        f"fails when over {REGRESSION_LIMIT - 1:.0%} and over {REGRESSION_FLOOR_MS} ms slower.\n\n"
        f"| Phase | Baseline | This branch | Change | |\n|---|---|---|---|---|\n" + "\n".join(rows))
    assert not failed, f"start-up slower than the baseline in: {', '.join(failed)}"


# ---- D-052: usable on a phone (owner, 27 Nov 2026) -----------------------------------------------------------------

def test_hover_label_names_the_object_under_the_pointer(page, viewer_url):
    """Pointing at a dot shows its name and details (pulled forward from roadmap 3.4), from the dataset's record."""
    open_viewer(page, viewer_url)
    records = {r["satcat_id"]: r for r in sample_records()["records"]}
    shown = page.evaluate("window.sattrackViewer.shownIds()")
    for satcat_id in shown:
        pos = page.evaluate(f"window.sattrackViewer.screenOf({satcat_id})")
        if not pos:
            continue
        page.evaluate(f"window.sattrackViewer.pointAt({pos['x']}, {pos['y']})")
        label = page.evaluate("window.sattrackViewer.label")
        if label and label["satcat_id"] == satcat_id:
            break
    else:
        raise AssertionError("no shown object could be pointed at")
    box = page.locator("#globe .sattrack-viewer-label")
    expect(box).to_be_visible()
    expect(box).to_contain_text(records[satcat_id]["object_name"])
    expect(box).to_contain_text(f"SATCAT {satcat_id}")
    page.mouse.move(5, 5)
    page.evaluate("window.sattrackViewer.pointAt(2, 2)")   # empty space: the label goes
    expect(box).to_be_hidden()
    assert page.errors == []


def test_idle_globe_draws_only_a_few_times_a_second(page, viewer_url):
    """Request-render mode (D-052): untouched, the globe draws when 0.25 s of simulation time has passed, not every
    frame; that is what keeps a phone free for the panel and filters."""
    open_viewer(page, viewer_url)
    page.wait_for_timeout(2000)
    before = page.evaluate("window.sattrackViewer.frameMs.length")
    page.wait_for_timeout(5000)
    per_second = (page.evaluate("window.sattrackViewer.frameMs.length") - before) / 5
    report(f"idle draws: {per_second:.1f} per second")
    assert 1 <= per_second <= 6
    assert page.errors == []


PHONE = {"viewport": {"width": 390, "height": 760}, "is_mobile": True, "has_touch": True, "device_scale_factor": 3}
PHONE_CPU = 4                     # CPU slowdown (Chrome DevTools throttling): a mid-range phone (D-027's 4x row)
PHONE_FILTER_S = 3.0              # click to dots updated, per filter change (5.7 s before D-052, 1.5 s after, locally)
PHONE_PANEL_S = 1.5               # Filters tapped to panel open (2.5 s before, 0.8 s after)
PHONE_BUSY = 0.6                  # share of the main thread in long tasks, 10-20 s after load (0.98 before, 0.32 after)


def test_phone_budget(browser, budget_url):
    """D-052: the tracker on a phone-sized page with the CPU slowed 4x and the full-size catalogue. Limits on the
    three things the owner found unusable: the main thread's load once started (it drew every frame), opening Filters
    (a server round trip) and a filter change (Dash re-reading ~40,000 dropdown options). Software WebGL on the CI
    runner draws on the CPU, so the limits leave room; each regression measured before D-052 is well past them."""
    context = browser.new_context(**PHONE)
    context.route(re.compile(r"^(?!http://127\.0\.0\.1[:/]).*"), lambda route: route.abort())
    page = context.new_page()
    try:
        page.add_init_script(LONG_TASKS)
        cdp = context.new_cdp_session(page)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": PHONE_CPU})
        open_viewer(page, budget_url)
        ready = page.evaluate("performance.now()")
        page.wait_for_timeout(10_000)
        t0 = page.evaluate("performance.now()")
        page.wait_for_timeout(10_000)
        t1 = page.evaluate("performance.now()")
        busy = sum(min(st + d, t1) - max(st, t0) for st, d in page.evaluate("window.__longTasks")
                   if st + d > t0 and st < t1) / (t1 - t0)
        start = time.time()
        page.locator("#toggle-filters").click()
        expect(page.locator("#filter-collapse")).to_have_class(re.compile(r"\bshow\b"), timeout=30_000)
        panel_s = time.time() - start
        page.wait_for_timeout(1500)
        changes = page.evaluate("window.sattrackViewer.filterChanges")
        start = time.time()
        page.locator("#status-filter-checkbox").get_by_text("Inactive", exact=True).click()
        wait_until(page, f"() => window.sattrackViewer.filterChanges > {changes}")
        filter_s = time.time() - start
        first = page.evaluate("window.sattrackViewer.firstPositionsMs")
        ok = lambda good: "ok" if good else "FAIL"  # noqa: E731
        job_summary(
            f"### Phone budget (D-052)\n\n390x760 at 3x, CPU slowed {PHONE_CPU}x, full-size catalogue, software WebGL.\n\n"
            f"| Check | Value | Limit | |\n|---|---|---|---|\n"
            f"| Main thread in long tasks, 10-20 s after load | {busy:.0%} | {PHONE_BUSY:.0%} | {ok(busy <= PHONE_BUSY)} |\n"
            f"| Filters tapped to open | {panel_s:.2f} s | {PHONE_PANEL_S} s | {ok(panel_s <= PHONE_PANEL_S)} |\n"
            f"| Filter change, click to dots updated | {filter_s:.2f} s | {PHONE_FILTER_S} s | "
            f"{ok(filter_s <= PHONE_FILTER_S)} |\n"
            f"| First positions | {first:,.0f} ms (viewer start {ready:,.0f} ms after navigation) | reported | |")
        assert busy <= PHONE_BUSY
        assert panel_s <= PHONE_PANEL_S
        assert filter_s <= PHONE_FILTER_S
    finally:
        context.close()
