"""TEMPORARY diagnostic (removed before merge): why CI visit times fall into two modes (PR #79).

Per visit to the branch app: the page's phases, the worker's own timestamps (worker.js DIAG), and from /proc the CPU
time and run-queue wait of every Chromium and server thread (grouped by process type and thread name), the
machine's CPU split (user/system/idle/steal) and load. A few browser configurations, 8 visits each."""
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from conftest import CHROMIUM_ARGS
from test_viewer import LONG_TASKS, job_summary, open_viewer

TICK_MS = 1000 / os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 10
NO_THROTTLE = ["--disable-renderer-backgrounding", "--disable-background-timer-throttling",
               "--disable-backgrounding-occluded-windows"]
CONFIGS = [
    ("default", CHROMIUM_ARGS, (1366, 900), ""),
    ("no-throttle", CHROMIUM_ARGS + NO_THROTTLE, (1366, 900), ""),
    ("render-after-ready", CHROMIUM_ARGS, (1366, 900), "window.__diagRenderAfterReady = true;"),
]
VISITS = int(os.environ.get("DIAG_VISITS", "6"))


def proc_snapshot():
    """{(process kind, thread name): [cpu ms, run-queue wait ms, run ms]} for Chromium and the app servers."""
    out = defaultdict(lambda: [0.0, 0.0, 0.0])
    proc = Path("/proc")
    if not proc.exists():
        return out
    for p in proc.iterdir():
        if not p.name.isdigit():
            continue
        try:
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if "serve.py" in cmd:
            kind = "server"
        elif "chrom" in cmd or "headless_shell" in cmd:
            m = re.search(r"--type=([\w-]+)", cmd)
            kind = m.group(1) if m else "browser"
            if kind == "utility":
                kind = "utility:" + (re.search(r"--utility-sub-type=([\w.]+)", cmd) or [None, "?"])[1].split(".")[-1]
        else:
            continue
        try:
            tasks = list((p / "task").iterdir())
        except OSError:
            continue
        for t in tasks:
            try:
                stat = (t / "stat").read_text()
                comm = stat[stat.index("(") + 1:stat.rindex(")")]
                f = stat[stat.rindex(")") + 2:].split()
                run, wait, _ = (t / "schedstat").read_text().split()
            except (OSError, ValueError):
                continue
            name = re.sub(r"\d+", "#", comm)
            row = out[(kind, name)]
            row[0] += (int(f[11]) + int(f[12])) * TICK_MS
            row[1] += int(wait) / 1e6
            row[2] += int(run) / 1e6
    return out


def cpu_split():
    try:
        v = [int(x) for x in Path("/proc/stat").read_text().split("\n")[0].split()[1:]]
    except OSError:
        return [0] * 10
    return v   # user nice system idle iowait irq softirq steal guest guest_nice


def visit(browser, url, viewport, script=""):
    context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
    context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
    context.add_init_script(LONG_TASKS + script)
    try:
        pg = context.new_page()
        s0, c0 = proc_snapshot(), cpu_split()
        open_viewer(pg, url)
        s1, c1 = proc_snapshot(), cpu_split()
        k = pg.evaluate("window.sattrackViewer.marks")
        origin = pg.evaluate("performance.timeOrigin")
        d = pg.evaluate("window.sattrackViewer.diag") or {}
        start = origin + k["start"]
        all_tasks = pg.evaluate("window.__longTasks || []")
        tasks = [x for (st, x) in all_tasks if st < k["firstPositions"]]
        lt = " ".join(f"{st - k['start']:.0f}+{x:.0f}" for st, x in all_tasks if st < k["firstPositions"] + 1500)
        frames = " ".join(f"{f[0] - k['start']:.0f}+{(f[1] - f[0]) if len(f) > 1 else -1:.0f}"
                          for f in (pg.evaluate("window.sattrackViewer.diagFrames") or [])[:6])
        threads = {f"{a}/{b}": [round(s1[(a, b)][i] - s0.get((a, b), [0, 0, 0])[i]) for i in range(3)]
                   for (a, b) in s1}
        dc = [b - a for a, b in zip(c0, c1)]
        tot = sum(dc) or 1
        return {
            "phases": {n: round(k[n] - k["start"]) for n in ("data", "cesium", "viewer", "ready", "firstPositions")},
            "worker": {n: round(v - start) for n, v in d.items()},
            "long_tasks": [round(x) for x in tasks],
            "lt": lt, "frames": frames,
            "threads": {n: v for n, v in threads.items() if v[0] >= 20 or v[1] >= 20},
            "cpu": {"user": round(100 * (dc[0] + dc[1]) / tot), "sys": round(100 * dc[2] / tot),
                    "idle": round(100 * dc[3] / tot), "steal": round(100 * dc[7] / tot)},
            "load": Path("/proc/loadavg").read_text().split()[0] if Path("/proc/loadavg").exists() else "",
        }
    finally:
        context.close()


def _trace_summary(path, start_epoch_ms):
    """Main-thread tasks over 300 ms in a Chrome trace: start, duration, and their biggest child events."""
    ev = json.loads(Path(path).read_text())
    ev = ev["traceEvents"] if isinstance(ev, dict) else ev
    names = {(e["pid"], e["tid"]): e["args"]["name"] for e in ev if e.get("ph") == "M" and e.get("name") == "thread_name"}
    main = {k for k, n in names.items() if n == "CrRendererMain"}
    # trace clock -> page clock: navigationStart-ish anchor via the first 'TracingStartedInBrowser' is unreliable;
    # report times relative to the first main-thread event instead, plus durations.
    xs = [e for e in ev if e.get("ph") == "X" and (e["pid"], e["tid"]) in main and "dur" in e]
    if not xs:
        return "no main-thread events"
    nav = [e["ts"] for e in ev if e.get("name") == "navigationStart" and (e["pid"], e["tid"]) in main]
    t0 = nav[-1] if nav else xs[0]["ts"]
    tasks = [e for e in xs if e["name"] == "ThreadControllerImpl::RunTask" and e["dur"] > 300_000]
    skip = {"ThreadControllerImpl::RunTask", "RunTask", "SimpleWatcher::OnHandleReady", "AsyncTask Run", "v8.run",
            "ScriptRunner::ExecutePendingScript", "PendingScript::ExecuteScriptBlock"}
    out = []
    for t in tasks:
        a, b = t["ts"], t["ts"] + t["dur"]
        kids = [e for e in xs if a <= e["ts"] < b and e is not t and e["dur"] > 20_000 and e["name"] not in skip]
        kids.sort(key=lambda e: -e["dur"])
        desc = []
        for k in kids[:10]:
            d = k.get("args", {}).get("data", {}) or {}
            extra = " ".join(str(x) for x in (d.get("functionName"), (d.get("url") or "")[-45:], d.get("lineNumber"),
                                              d.get("type")) if x)
            desc.append(f"{k['name']}{'(' + extra + ')' if extra else ''} {k['dur'] / 1000:.0f}")
        out.append(f"[at {(a - t0) / 1000 - start_epoch_ms:.0f} ms after viewer start, {t['dur'] / 1000:.0f} ms] "
                   + "; ".join(desc))
    return "\n  - ".join([""] + out)


def test_trace(browser, budget_url, tmp_path):
    """Chrome traces of default visits: what the ~650 ms main-thread task is."""
    b = browser.browser_type.launch(args=CHROMIUM_ARGS)
    rows = []
    try:
        visit(b, budget_url, (1366, 900))
        for i in range(8):
            context = b.new_context(viewport={"width": 1366, "height": 900})
            context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
            try:
                pg = context.new_page()
                path = tmp_path / f"trace{i}.json"
                b.start_tracing(page=pg, path=str(path), categories=[
                    "devtools.timeline", "v8", "v8.execute", "disabled-by-default-devtools.timeline", "blink",
                    "toplevel", "disabled-by-default-v8.gc", "gpu", "cc", "scheduler", "blink.user_timing"])
                open_viewer(pg, budget_url)
                k = pg.evaluate("window.sattrackViewer.marks")
                pg.wait_for_timeout(1500)
                b.stop_tracing()
                w = pg.evaluate("window.sattrackViewer.diag") or {}
                origin = pg.evaluate("performance.timeOrigin")
                rows.append(f"visit {i}: data {k['data'] - k['start']:.0f}, worker computed "
                            f"{w.get('computed', 0) - origin - k['start']:.0f}, ready {k['ready'] - k['start']:.0f}, "
                            f"first {k['firstPositions'] - k['start']:.0f} {_trace_summary(path, k['start'])}")
            finally:
                context.close()
    finally:
        b.close()
    job_summary("### DIAG trace (temporary)\n\n" + "\n\n".join(rows))


def test_diag(browser, budget_url):
    lines = [f"cpus {os.cpu_count()}, affinity {len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else '?'}"]
    table = ["| config | # | data | cesium | viewer | ready | first | w.fetched | w.parsed | w.buildStart | w.built | "
             "w.computed | long tasks | worker thr cpu/wait | main thr cpu/wait | gpu cpu | pool cpu/wait | "
             "user/idle/steal | long tasks start+ms | frames start+ms |",
             "|" + "---|" * 20]
    raw = []
    for name, args, viewport, script in CONFIGS:
        b = browser.browser_type.launch(args=args)
        try:
            visit(b, budget_url, viewport, script)   # warm-up, discarded
            for i in range(VISITS):
                v = visit(b, budget_url, viewport, script)
                raw.append({"config": name, "i": i, **v})
                th, w, ph = v["threads"], v["worker"], v["phases"]

                def grp(pred):
                    rows = [x for n, x in th.items() if pred(n)]
                    return f"{sum(r[0] for r in rows)}/{sum(r[1] for r in rows)}"
                table.append(
                    f"| {name} | {i} | {ph['data']} | {ph['cesium']} | {ph['viewer']} | {ph['ready']} | "
                    f"{ph['firstPositions']} | {w.get('fetched', '')} | {w.get('parsed', '')} | "
                    f"{w.get('buildStart', '')} | {w.get('built', '')} | {w.get('computed', '')} | "
                    f"{len(v['long_tasks'])} ({sum(v['long_tasks'])}) | "
                    f"{grp(lambda n: n == 'renderer/DedicatedWorker')} | "
                    f"{grp(lambda n: n == 'renderer/chrome-headless')} | "
                    f"{grp(lambda n: n.startswith('gpu-process/'))} | "
                    f"{grp(lambda n: n == 'renderer/ThreadPoolForeg')} | "
                    f"{v['cpu']['user']}/{v['cpu']['idle']}/{v['cpu']['steal']} | {v['lt']} | {v['frames']} |")
        finally:
            b.close()
    job_summary("### DIAG: visit modes (temporary)\n\n" + "\n".join(lines) + "\n\n" + "\n".join(table))
    # every thread group, for the slowest and fastest default visits
    for r in raw:
        print("DIAGJSON " + json.dumps(r))
    job_summary("DIAG raw\n\n```\n" + "\n".join(json.dumps(r) for r in raw) + "\n```")
