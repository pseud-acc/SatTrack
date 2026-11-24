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
VISITS = int(os.environ.get("DIAG_VISITS", "10"))


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
