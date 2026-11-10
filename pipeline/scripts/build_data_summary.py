"""Build the data summary dashboard (dbt Charts) from the dbt analyses in transform/analyses/data_summary/.

Steps:
  1. `dbt parse` against the live DB, so ref() in the analyses resolves to the live database's relations.
  2. Generate transform/charts/_generated/data_summary_queries.yml from the manifest:
       * one query per analysis (SQL copied verbatim, description as the query note), so the analyses stay
         the single, audited home of every query (dbt Charts has no file include);
       * the field catalogue: every column of the app mart with its documented description and origin.
  3. `dct render` transform/charts/data_summary.yml once per tab (dct's static HTML draws only the selected
     tab) and stack the panels into one self-contained data/reports/data_summary.html, with the tab strip
     rewired to in-page anchors (#overview, #objects, ...). The previous report is kept if this fails.

Rules enforced on every build (the build fails, writing nothing, if one breaks):
  * every analysis reads only the app mart (MART), so the dashboard describes exactly what the app shows;
  * every analysis has a description in _data_summary__analyses.yml;
  * analyses use no Jinja other than ref(), which dbt Charts resolves itself.

Run with the dbt Charts venv's Python (it provides PyYAML and `dct`):
  python scripts/build_data_summary.py            # parse, generate, render
  python scripts/build_data_summary.py --check    # parse, generate, `dct validate` only (CI)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
from sattrack_ingest.config import DATA_DIR, LIVE_DB, OPS_DB  # noqa: E402

TRANSFORM = ROOT / "transform"
ANALYSES_DIR = "analyses/data_summary"
BOARD = Path("charts") / "data_summary.yml"
GENERATED = TRANSFORM / "charts" / "_generated" / "data_summary_queries.yml"
OUT = DATA_DIR / "reports" / "data_summary.html"
MART = "fct__satellite_master"
TAB_VAR = "_tab_sattrack_data_summary"   # dct's tab variable for this board: _tab_<project>_<board file stem>
DBT = os.environ.get("SATTRACK_DBT_BIN", "dbt")
DCT = os.environ.get("SATTRACK_DCT_BIN") or str(Path(sys.executable).with_name("dct"))

_REF = re.compile(r"\{\{\s*ref\(\s*'([^']+)'\s*\)\s*\}\}")
_JINJA = re.compile(r"\{\{|\{%|\{#")
_SOURCE_URL = re.compile(r"Sources?:\s*(\S+)")
# a column's origin, from the publisher page its documented definition cites
_ORIGIN_BY_URL = [
    ("space-track.org", "Space-Track"),
    ("planet4589.org/space/gcat/web/intro", "Computed (SatTrack rule)"),
    ("planet4589.org", "GCAT"),
    ("celestrak", "CelesTrak"),
]


class BuildError(Exception):
    pass


def _dct_env() -> dict:
    """dbt Charts joins the profile's DuckDB path onto the project dir on Windows, so pass relative paths."""
    return dict(os.environ,
                SATTRACK_DB_PATH=os.path.relpath(LIVE_DB, TRANSFORM).replace("\\", "/"),
                SATTRACK_OPS_PATH=os.path.relpath(OPS_DB, TRANSFORM).replace("\\", "/"),
                DCT_NO_WORKSPACE_GUARD="1")


def parse_manifest() -> dict:
    """Parse against the live DB: the manifest's relation names carry the DB file's name, which is what
    dbt Charts uses for ref()."""
    env = dict(os.environ, SATTRACK_DB_PATH=str(LIVE_DB), SATTRACK_OPS_PATH=str(OPS_DB))
    res = subprocess.run([DBT, "parse", "--profiles-dir", str(TRANSFORM)], cwd=TRANSFORM, env=env,
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise BuildError(f"dbt parse failed:\n{(res.stdout + res.stderr)[-2000:]}")
    return json.loads((TRANSFORM / "target" / "manifest.json").read_text(encoding="utf-8"))


def analysis_queries(manifest: dict) -> dict:
    nodes = [n for n in manifest["nodes"].values()
             if n["resource_type"] == "analysis" and n["original_file_path"].replace("\\", "/").startswith(ANALYSES_DIR)]
    if not nodes:
        raise BuildError(f"no analyses found under transform/{ANALYSES_DIR}")
    problems, queries = [], {}
    for n in sorted(nodes, key=lambda x: x["name"]):
        sql = n["raw_code"].replace("\r\n", "\n").strip() + "\n"
        refs = set(_REF.findall(sql))
        if refs != {MART}:
            problems.append(f"{n['name']}: must read only {MART}, reads {sorted(refs) or 'nothing'}")
        if _JINJA.search(_REF.sub("", sql)):
            problems.append(f"{n['name']}: uses Jinja other than ref(), which dbt Charts cannot run")
        if not (n.get("description") or "").strip():
            problems.append(f"{n['name']}: no description in _data_summary__analyses.yml")
        queries[n["name"]] = {"notes": f"{n['original_file_path']}: {n.get('description', '').strip()}", "sql": sql}
    if problems:
        raise BuildError("analysis rules broken:\n  " + "\n  ".join(problems))
    return queries


def field_catalogue(manifest: dict) -> tuple[dict, dict]:
    """Every column of the app mart with its description and origin (values queries, built from the yml docs)."""
    model = manifest["nodes"].get(f"model.sattrack.{MART}")
    if not model:
        raise BuildError(f"{MART} not in the manifest")
    names = list(model["columns"])
    rows, counts = [], {}
    for name, col in model["columns"].items():
        desc = " ".join((col.get("description") or "").split())
        url = (_SOURCE_URL.findall(desc) or [""])[-1]
        if name in ("inserted_date_time", "inserted_by"):
            origin = "Audit"
        elif f"{name}_source" in names or name == "jcat":
            origin = "Resolved across sources"
        elif name.endswith(("_source", "_method", "_precision")):
            origin = "Provenance"
        elif not desc:
            origin = "Undocumented"
        else:
            origin = next((o for key, o in _ORIGIN_BY_URL if key in url), "Other")
        summary = _SOURCE_URL.split(desc)[0].strip()
        rows.append([name, col.get("data_type") or "", origin, summary[:220] + ("..." if len(summary) > 220 else ""), url])
        counts[origin] = counts.get(origin, 0) + 1
    catalogue = {"notes": f"Generated from the {MART} yml column docs (manifest).",
                 "columns": ["column_name", "data_type", "origin", "definition", "cited_source"], "values": rows}
    origin_counts = {"notes": f"Generated: {MART} columns per origin.", "columns": ["origin", "columns"],
                     "values": [[o, c] for o, c in sorted(counts.items(), key=lambda kv: -kv[1])]}
    return catalogue, origin_counts


class _Literal(str):
    pass


def _dump(data: dict) -> str:
    yaml.SafeDumper.add_representer(_Literal, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"))
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10_000)


def write_queries(manifest: dict) -> None:
    queries = {name: {"notes": q["notes"], "sql": _Literal(q["sql"])} for name, q in analysis_queries(manifest).items()}
    catalogue, origin_counts = field_catalogue(manifest)
    queries["gen__field_catalogue"] = catalogue
    queries["gen__field_origin_counts"] = origin_counts
    header = ("# GENERATED by scripts/build_data_summary.py - do not edit.\n"
              f"# SQL comes from transform/{ANALYSES_DIR}/*.sql; edit it there.\n")
    GENERATED.parent.mkdir(parents=True, exist_ok=True)
    GENERATED.write_text(header + _dump({"queries": queries}), encoding="utf-8")


def dct(*args: str) -> None:
    res = subprocess.run([DCT, *args], cwd=TRANSFORM, env=_dct_env(), capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise BuildError(f"dct {args[0]} failed:\n{(res.stdout + res.stderr)[-4000:]}")


def _tab_slugs() -> list[str]:
    """dbt Charts names each tab by its title, lower-cased with non-alphanumerics as underscores."""
    board = yaml.safe_load((TRANSFORM / BOARD).read_text(encoding="utf-8"))
    return [re.sub(r"[^a-z0-9]+", "_", item["title"].lower()).strip("_") for item in board["tabs"]["items"]]


_BOARD_DIV = re.compile(r'<div class="dbt-charts-svg-container dbt-charts-board" data-dbt-board>.*?</svg>\s*</div>', re.S)
_TAB_LINK = re.compile(r'href="\?[^"]*?_tab_' + TAB_VAR.removeprefix("_tab_") + r'=([a-z0-9_]+)"')
_SERVER_LINK = re.compile(r'href="\?[^"]*"')   # any other dct-serve link (it would leak local paths)
_SWITCHER = """
<style>.ds-tab[hidden]{display:none}</style>
<script>
(function () {
  function show() {
    var want = (location.hash || '').slice(1), tabs = document.querySelectorAll('.ds-tab'), found = false;
    tabs.forEach(function (t) { if (t.dataset.tab === want) { found = true; } });
    tabs.forEach(function (t, i) { t.hidden = found ? t.dataset.tab !== want : i !== 0; });
  }
  window.addEventListener('hashchange', show);
  show();
})();
</script>
"""


def render_html(out: Path) -> None:
    """dct's static HTML draws only the selected tab, and its tab strip links back to a `dct serve` server.
    Render the board once per tab, then stack the panels in one file with the tab links as in-page anchors."""
    slugs = _tab_slugs()
    work = out.parent / "_render"
    work.mkdir(parents=True, exist_ok=True)
    cache = work / "query_cache.duckdb"
    cache.unlink(missing_ok=True)
    pages = []
    for slug in slugs:
        page = work / f"{slug}.html"
        dct("render", str(BOARD), "--format", "html", "--no-warnings", "--cache", str(cache),
            "--var", f"{TAB_VAR}={slug}", "--output", str(page))
        pages.append(page.read_text(encoding="utf-8"))
    panels = []
    for slug, page in zip(slugs, pages):
        board = _BOARD_DIV.search(page)
        if not board:
            raise BuildError(f"tab {slug}: board markup not found in the dct output (dct version change?)")
        markup = _SERVER_LINK.sub('href="#"', _TAB_LINK.sub(lambda m: f'href="#{m.group(1)}"', board.group(0)))
        panels.append(f'<div class="ds-tab" data-tab="{slug}">{markup}</div>')
    first = pages[0]
    head, tail = first[: first.index("<body>")], "</body>\n</html>\n"
    out.write_text(head + '<body>\n<div class="dbt-charts-wrapper">\n' + "\n".join(panels) + "\n</div>\n"
                   + _SWITCHER + tail, encoding="utf-8")
    for p in work.iterdir():
        p.unlink()
    work.rmdir()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="validate only; do not render")
    args = ap.parse_args()
    try:
        write_queries(parse_manifest())
        if args.check:
            dct("validate", str(BOARD))
            print("data summary: ok")
            return 0
        OUT.parent.mkdir(parents=True, exist_ok=True)
        tmp = OUT.with_suffix(".tmp.html")
        render_html(tmp)
        os.replace(tmp, OUT)   # keep the last good report if rendering fails
        print(f"data summary: {OUT}")
        return 0
    except BuildError as exc:
        print(f"data summary: FAILED - {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
