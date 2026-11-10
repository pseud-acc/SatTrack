"""Per-run summary log: the command and the result of each stage (status, duration, counts, anything not passing).

One file per run at <DATA_DIR>/logs/YYYY/MM/DD/<run_id>.log, the same relative path the remote run uploads to
S3 (logs/YYYY/MM/DD/<run_id>.log). Never the dbt output itself: dbt detail lives in Elementary and audit.*.
Plain text, no secrets: errors pass through audit.scrub() before they reach a stage.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

LOG_SUBDIR = "logs"


def log_path(data_dir: Path, run_id: str, started: datetime) -> Path:
    return data_dir / LOG_SUBDIR / f"{started:%Y}" / f"{started:%m}" / f"{started:%d}" / f"{run_id}.log"


def _duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    seconds = round(seconds)
    return f"{seconds // 60}m {seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


def _detail(stage: dict) -> list[str]:
    """One summary line plus any indented lines for things that did not pass."""
    name, extra = stage["stage"], []
    if "error" in stage:
        return [f"error: {stage['error']}"]
    if name.startswith("ingest:"):
        rows = stage.get("rows") or {}
        loaded = [f"{t}={n:,}" for t, n in rows.items() if isinstance(n, int)]
        # skipped tables come as {"<table>": "skipped_fresh"} or, from Space-Track, {"skipped_fresh": [tables]}
        fresh = [t for t, n in rows.items() if n == "skipped_fresh"] + list(rows.get("skipped_fresh") or [])
        parts = []
        if loaded:
            parts.append("rows " + ", ".join(loaded))
        if fresh:
            parts.append(f"skipped as fresh: {', '.join(fresh)}")
        return ["; ".join(parts)]
    if name == "source_freshness":
        line = f"{stage.get('sources', 0)} sources checked"
        return [line] + [f"  not pass: {x}" for x in stage.get("not_pass", [])]
    if name.startswith("dbt:"):
        counts = ", ".join(f"{k}={v}" for k, v in sorted((stage.get("statuses") or {}).items()))
        line = f"{counts}; exit {stage.get('exit_code')}"
        if stage.get("reason"):
            line = stage["reason"]
        extra = [f"  {i['status']}: {i['node']}" + (f" ({i['failures']} rows)" if i.get("failures") else "")
                 for i in stage.get("issues", [])]
        return [line] + extra
    if name == "orphan_cleanup":
        dropped = stage.get("dropped") or []
        return [f"dropped {len(dropped)}: {', '.join(dropped)}" if dropped else "nothing to drop"]
    if name == "raw_history_prune":
        return [f"removed {stage.get('removed', 0)} old raw files"]
    return [stage.get("detail") or stage.get("reason") or ""]


def render(*, run_id: str, command: str, trigger: str, git_sha: str | None, versions: dict,
           started: datetime, finished: datetime, overall: str, units: dict, stages: list[dict],
           reports: dict, row_changes: list[tuple[str, int, int | None]], crash: str | None = None) -> str:
    out = [
        f"SatTrack run {run_id}",
        f"command   {command}",
        f"trigger   {trigger}    git {git_sha or 'n/a'}    " + "  ".join(f"{k} {v}" for k, v in versions.items()),
        f"started   {started:%Y-%m-%d %H:%M:%S} UTC",
        f"finished  {finished:%Y-%m-%d %H:%M:%S} UTC  ({_duration((finished - started).total_seconds())})",
        f"result    {overall.upper()}    " + "  ".join(f"{u}={s}" for u, s in units.items()),
    ]
    if crash:
        out.append(f"crashed   {crash}")
    out += ["", "stages"]
    width = max((len(s["stage"]) for s in stages), default=10)
    for s in stages:
        first, *rest = _detail(s) or [""]
        out.append(f"  {s['stage']:<{width}}  {s['status']:<7} {_duration(s.get('duration_s')):>7}  {first}".rstrip())
        out += [f"  {'':<{width}}  {'':<7} {'':>7}  {line}" for line in rest]
    if reports:
        out += ["", "reports   " + "  ".join(f"{k}={'ok' if v == 0 else f'exit {v}'}" for k, v in reports.items())]
    if row_changes:
        out += ["", "mart rows (change since previous run)"]
        w = max(len(t) for t, _, _ in row_changes)
        for table, n, prev in row_changes:
            delta = "new" if prev is None else (f"{n - prev:+,}" if n != prev else "no change")
            out.append(f"  {table:<{w}}  {n:>10,}  {delta}")
    return "\n".join(out) + "\n"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
