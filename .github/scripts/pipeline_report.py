"""Public run report for pipeline.yml, and the alerts.

Problems exit 1: the job fails and GitHub emails the owner. Warnings don't fail the job (a run whose units all
published is a good run): the report hands their summary to the workflow's `notify` job, which posts it to the
"Pipeline warnings" issue so GitHub emails it (D-037). Each warning shows how long it has been warning.

Prints to the public Actions log and the run's summary page only what is safe to publish: the overall result,
each stage's name and status, the names of dbt checks that did not pass, and the dates of the data the app now
serves. Never row data, identifiers of objects, credentials or the private log's other content.

A problem is any of:
  * the pipeline exited non-zero, a unit didn't publish (held or error), or no run summary exists
  * committing the state to S3 failed
  * the published positions are older than MAX_POSITIONS_AGE_H, or the details older than MAX_DETAILS_AGE_D
A warning is a dbt check at warn severity or a source past its freshness limit, in a run with no problem.
A run skipped by the 12-hour gate is neither: a run's data went live less than 12 hours ago.

Inputs (environment): SATTRACK_DATA_DIR, GATE ('true' if the pipeline ran), PIPELINE_EXIT, PUSH_OUTCOME,
GITHUB_STEP_SUMMARY and GITHUB_OUTPUT (set by Actions).
Outputs (GITHUB_OUTPUT): status = problem | warning | ok | skipped; body = the Markdown summary for the issue.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_POSITIONS_AGE_H = 30      # daily run at 03:17 UTC, plus slack for a late or retried run
MAX_DETAILS_AGE_D = 14        # owner's rule: GCAT details may be up to 14 days stale

STAGE = re.compile(r"^  (\S+)\s+(ok|warn|error|held|skipped|failed|crashed|fail)\b", re.I)
SINCE = r"(?: since (\d{4}-\d\d-\d\d \d\d:\d\d) UTC \((\d+) runs?\))?"   # runlog.since_suffix
ISSUE = re.compile(r"^\s+(fail|error|warn|skipped): (\S+)(?: \((\d+) rows\))?" + SINCE)
FRESHNESS = re.compile(r"^\s+not pass: (\S+) (\w+): ([\d.]+ h old \(warn after [^)]*\))" + SINCE)


def _parse_ts(value):
    if not value:
        return None
    ts = datetime.fromisoformat(value)
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _age(ts, now):
    return None if ts is None else (now - ts).total_seconds()


def _for_how_long(since, runs, now):
    """', warning for 2.1 days (3 runs, since 2026-11-21 03:18 UTC)' from a run log's since/runs, or ''."""
    if not since:
        return ""
    start = datetime.strptime(since, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    days = max((now - start).total_seconds(), 0) / 86400
    return f", warning for {days:.1f} days ({runs} run{'s' if runs != '1' else ''}, since {since} UTC)"


def _output(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            for k, v in values.items():
                fh.write(f"{k}<<SATTRACK_EOF\n{v}\nSATTRACK_EOF\n")


def main() -> int:
    now = datetime.now(timezone.utc)
    data_dir = Path(os.environ.get("SATTRACK_DATA_DIR", ""))
    lines, problems, warnings = [], [], []

    if os.environ.get("GATE") != "true":
        msg = "Pipeline skipped by the 12-hour gate: a run's data went live less than 12 hours ago."
        print(msg)
        _summary([f"**Skipped.** {msg}"])
        _output(status="skipped", body=msg)
        return 0

    exit_code = os.environ.get("PIPELINE_EXIT") or "none"
    if exit_code != "0":
        problems.append(f"pipeline exit code {exit_code}")
    if os.environ.get("PUSH_OUTCOME") not in ("success", "skipped"):
        problems.append(f"committing state to S3: {os.environ.get('PUSH_OUTCOME') or 'did not run'}")

    # Run summary (data/logs/YYYY/MM/DD/<run_id>.log): result, stages, checks that did not pass
    logs = sorted((data_dir / "logs").rglob("run_*.log"), key=lambda p: p.stat().st_mtime) if data_dir.name else []
    result = "missing"
    if logs:
        text = logs[-1].read_text(encoding="utf-8", errors="replace").splitlines()
        result_line = next((l for l in text if l.startswith("result")), "")
        result = result_line.split()[1] if len(result_line.split()) > 1 else "missing"
        units = dict(u.split("=", 1) for u in result_line.split()[2:] if "=" in u)
        lines.append(f"Result: {' '.join(result_line.split()[1:]) or 'missing'}")
        stages, issues, skipped = [], [], 0
        for l in text:
            m = STAGE.match(l)
            if m:
                stages.append(f"{m.group(1)}={m.group(2).lower()}")
            i = ISSUE.match(l)
            f = FRESHNESS.match(l)
            if i and i.group(1) == "skipped":
                skipped += 1
            elif i:
                issues.append(f"{i.group(1)}: {i.group(2)}" + (f" ({i.group(3)} rows)" if i.group(3) else "")
                              + _for_how_long(i.group(4), i.group(5), now))
                if i.group(1) == "warn":
                    warnings.append(issues[-1])
            elif f:
                issues.append(f"freshness {f.group(2)}: {f.group(1)} {f.group(3)}"
                              + _for_how_long(f.group(4), f.group(5), now))
                warnings.append(issues[-1])
        lines.append("Stages: " + ", ".join(stages))
        if issues:
            lines.append("Checks not passing:")
            lines += [f"  - {x}" for x in issues]
        if skipped:
            lines.append(f"  ({skipped} downstream models/tests skipped)")
    else:
        units = {}
        lines.append("Result: no run summary written")
    # WARN with every unit published is a good run with warnings; a held or failed unit is a problem.
    if result not in ("OK", "WARN") or (result == "WARN" and (not units or any(v != "ok" for v in units.values()))):
        problems.append(f"pipeline result {result}")

    # Dates of the data the app serves (export manifest, written with the app CSVs)
    manifest_path = data_dir / "app" / "manifest.json"
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        pos = _parse_ts(m.get("positions_as_of"))
        det = _parse_ts(m.get("details_built_at") or m.get("mart_built_at"))
        gcat = _parse_ts(m.get("gcat_updated_at"))
        pos_age, det_age = _age(pos, now), _age(det, now)
        lines.append(f"Positions (Space-Track GP) as of: {pos:%Y-%m-%d %H:%M UTC} ({pos_age / 3600:.1f} h ago)"
                     if pos else "Positions as of: unknown")
        lines.append(f"Details (GCAT) built: {det:%Y-%m-%d %H:%M UTC} ({det_age / 86400:.1f} days ago)"
                     + (f", GCAT catalogue updated {gcat:%Y-%m-%d}" if gcat else "") if det else "Details built: unknown")
        if pos_age is None or pos_age > MAX_POSITIONS_AGE_H * 3600:
            problems.append(f"positions older than {MAX_POSITIONS_AGE_H} h")
        if det_age is None or det_age > MAX_DETAILS_AGE_D * 86400:
            problems.append(f"details older than {MAX_DETAILS_AGE_D} days")
    else:
        lines.append("App files: none exported this run")
        problems.append("no app export")

    for l in lines:
        print(l)
    head = ("**Problems:** " + "; ".join(problems) if problems
            else f"**Warnings:** {len(warnings)}, data published" if warnings else "**OK**")
    _summary([head, ""] + [f"    {l}" for l in lines] + ["", "Details are in the private log in S3."])
    status = "problem" if problems else "warning" if warnings else "ok"
    _output(status=status, body="\n".join([head, "", "```"] + lines + ["```", "", "Details are in the private log in S3."]))
    if problems:
        # One annotation per run: shows on the run page; the failed job makes GitHub email the owner.
        print(f"::error title=SatTrack pipeline needs attention::{'; '.join(problems)}")
        return 1
    if warnings:
        # Not a failure: the data went live. The notify job emails this summary through the warnings issue.
        print(f"::warning title=SatTrack pipeline warnings::{len(warnings)} warning(s); data published")
    return 0


def _summary(md_lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("## SatTrack pipeline run\n\n" + "\n".join(md_lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
