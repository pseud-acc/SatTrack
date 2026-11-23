"""Measure the Cesium spike page (roadmap 3.1). Throwaway spike tooling, not part of the app.

    python measure.py parity <data folder> [base url]       browser positions vs the Python sgp4 library
    python measure.py perf   <out.json> [base url] [secs]   FPS, main-thread and worker cost, load, heap, CPU throttled

Needs serve.py running on the same data folder, and Playwright with Chromium. Chromium is started with the real GPU
(ANGLE on D3D11); CPU throttling uses the DevTools protocol, which slows the page's main thread only, not workers.
"""
import gzip
import json
import math
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

GPU_ARGS = ["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=d3d11"]
WHEN = "2026-11-22T12:00:00Z"


def open_page(browser, url, throttle=1):
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    cdp = page.context.new_cdp_session(page)
    cdp.send("Performance.enable")
    if throttle > 1:
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": throttle})
    page.goto(url)
    page.wait_for_function("window.spike && (window.spike.ready || window.spike.error)", timeout=300000)
    err = page.evaluate("window.spike.error")
    if err:
        raise RuntimeError(f"{url}: {err}")
    return page, cdp, errors


def python_positions(data_dir):
    """ECF positions (km) at WHEN from the sgp4 library, the same OMM fields and the same GMST rotation."""
    from sgp4 import omm
    from sgp4.api import Satrec, jday
    from sgp4.propagation import gstime

    records = json.loads(gzip.decompress((Path(data_dir) / "objects.json.gz").read_bytes()))["records"]
    jd, fr = jday(2026, 11, 22, 12, 0, 0)
    g = gstime(jd + fr)
    out, errors = {}, {}
    for r in records:
        fields = {"OBJECT_NAME": r["object_name"], "OBJECT_ID": r["object_id"], "NORAD_CAT_ID": r["satcat_id"],
                  "EPOCH": r["epoch"], "MEAN_MOTION": r["mean_motion"], "ECCENTRICITY": r["eccentricity"],
                  "INCLINATION": r["inclination"], "RA_OF_ASC_NODE": r["ra_of_asc_node"],
                  "ARG_OF_PERICENTER": r["arg_of_pericenter"], "MEAN_ANOMALY": r["mean_anomaly"],
                  "EPHEMERIS_TYPE": r["ephemeris_type"], "CLASSIFICATION_TYPE": r["classification_type"],
                  "ELEMENT_SET_NO": r["element_set_no"], "REV_AT_EPOCH": r["rev_at_epoch"], "BSTAR": r["bstar"],
                  "MEAN_MOTION_DOT": r["mean_motion_dot"], "MEAN_MOTION_DDOT": r["mean_motion_ddot"]}
        sat = Satrec()
        try:
            omm.initialize(sat, {k: str(v) for k, v in fields.items()})
        except Exception as e:  # noqa: BLE001 - spike tooling: record and carry on
            errors[r["satcat_id"]] = f"init: {e}"
            continue
        e, p, _ = sat.sgp4(jd, fr)
        if e:
            errors[r["satcat_id"]] = f"sgp4 error {e}"
            continue
        c, s = math.cos(g), math.sin(g)
        out[r["satcat_id"]] = (p[0] * c + p[1] * s, -p[0] * s + p[1] * c, p[2])
    return out, errors


def parity(data_dir, base):
    py, py_err = python_positions(data_dir)
    report = {"when": WHEN, "python_ok": len(py), "python_errors": py_err}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=GPU_ARGS)
        for engine in ("js", "wasm", "worker&wengine=js", "worker&wengine=wasm"):
            page, _, _ = open_page(browser, f"{base}?engine={engine}&spin=0")
            rows = page.evaluate(f"window.spike.snapshot('{WHEN}')")
            page.close()
            got = {r[0]: r[1:] for r in rows}
            diffs, only_browser, only_python, missing = [], [], [], []
            for sid in set(got) | set(py) | set(py_err):
                b, q = got.get(sid), py.get(sid)
                b_ok = b is not None and all(v is not None and math.isfinite(v) for v in b)
                if b_ok and q:
                    diffs.append((math.dist(b, q), sid))
                elif b_ok:
                    only_browser.append([sid, py_err.get(sid), b])
                elif q:
                    only_python.append([sid, "rejected at parse" if b is None else "NaN"])
            diffs.sort()
            n = len(diffs)
            report[engine] = {
                "compared": n, "max_km": diffs[-1][0] if n else None, "worst": [[s, d] for d, s in diffs[-5:]],
                "p99_km": diffs[int(0.99 * (n - 1))][0] if n else None, "over_1m": sum(d > 0.001 for d, _ in diffs),
                "browser_only": only_browser, "python_only": only_python,
            }
        browser.close()
    print(json.dumps(report, indent=1, default=str))


RUNS = [  # (label, query)
    ("js main/frame, all", "engine=js&rate=frame"),
    ("wasm main/frame, all", "engine=wasm&rate=frame"),
    ("worker js 1s+interp, all", "engine=worker&wengine=js&step=1"),
    ("worker wasm 1s+interp, all", "engine=worker&wengine=wasm&step=1"),
    ("wasm main/frame, payloads", "engine=wasm&rate=frame&types=PAYLOAD"),
    ("worker wasm 1s+interp, payloads", "engine=worker&wengine=wasm&step=1&types=PAYLOAD"),
]


def perf(out, base, secs):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=GPU_ARGS)
        for throttle in (1, 4, 6):
            for label, query in RUNS:
                t0 = time.time()
                page, cdp, errors = open_page(browser, f"{base}?{query}", throttle)
                page.wait_for_timeout(3000)
                page.evaluate("for (const k of ['frameMs','propMs','applyMs','workerMs']) if (window.spike[k]) window.spike[k].length = 0")
                page.wait_for_timeout(int(secs * 1000))
                s = page.evaluate("""() => { const s = window.spike, m = s.marks;
                    const avg = a => a && a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
                    const p95 = a => { if (!a || !a.length) return null; const b = [...a].sort((x, y) => x - y);
                                        return b[Math.floor(0.95 * (b.length - 1))]; };
                    return {engine: s.engine, rate: s.rate, count: s.count, failed: s.failed,
                            hidden: s.propagationFailures, load_ms: m.firstPositions - m.start,
                            fps: 1000 / avg(s.frameMs), frame_p95_ms: p95(s.frameMs),
                            main_ms: avg(s.propMs), apply_ms: avg(s.applyMs), worker_ms: avg(s.workerMs),
                            frames: s.frameMs.length}; }""")
                metrics = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
                s.update(label=label, throttle=throttle, heap_mb=metrics.get("JSHeapUsedSize", 0) / 1e6,
                         wall_s=round(time.time() - t0, 1), errors=errors[:3])
                print(json.dumps(s), flush=True)
                results.append(s)
                page.close()
        browser.close()
    Path(out).write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "parity":
        parity(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8765/")
    else:
        perf(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8765/",
             float(sys.argv[4]) if len(sys.argv) > 4 else 8)
