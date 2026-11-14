"""Contract helper. The committed yml is the contract (decided 2026-10-25); this script never rewrites it.

  --check               Compare every model in the dbt manifest with its built table. Exit 1 when a contracted
                        model's columns or types differ from its yml, or when a yml documents a column that the
                        model no longer produces. Run in CI after `dbt build`.
  --scaffold MODEL      Print a starting yml block for a newly built model (description from the SQL header
                        comment, columns, doc() links from the docs registry, model_health stubs). Contract types
                        and key constraints are included for marts. Paste it into the folder's _<folder>__schema.yml
                        and finish the TODOs by hand.

The database defaults to the pipeline's build copy; override with --db (e.g. the dev copy).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
from sattrack_ingest.config import BUILD_DB, connect  # noqa: E402

TRANSFORM = ROOT / "transform"
REGISTRY = TRANSFORM / "docs" / "columns_registry.md"
SCHEMAS = ("staging", "intermediate", "marts", "marts_tracking")


def built_columns(con, model: str) -> list[tuple[str, str]]:
    return con.execute(
        "select column_name, lower(data_type) from information_schema.columns "
        "where table_name = ? and table_schema in (?, ?, ?, ?) order by ordinal_position", [model, *SCHEMAS]).fetchall()


def check(con, manifest_path: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    problems = []
    for node in manifest["nodes"].values():
        if node.get("resource_type") != "model" or node.get("package_name") != "sattrack":
            continue
        name = node["name"]
        built = built_columns(con, name)
        if not built:
            problems.append(f"{name}: not built in this database")
            continue
        built_names = [c for c, _ in built]
        declared = node.get("columns", {})
        for col in declared:
            if col not in built_names:
                problems.append(f"{name}: yml documents '{col}', which the model no longer produces")
        if (node.get("config", {}).get("contract") or {}).get("enforced"):
            yml = [(c["name"], (c.get("data_type") or "").lower()) for c in declared.values()]
            if [c for c, _ in yml] != built_names:
                missing = [c for c in built_names if c not in declared]
                problems.append(f"{name}: contract columns differ from the build (undeclared: {missing})")
            for (col, want), (_, got) in zip(yml, built):
                if want and want != got:
                    problems.append(f"{name}.{col}: contract type {want}, built type {got}")
    for p in problems:
        print("CONTRACT DRIFT", p)
    print(f"checked {sum(1 for n in manifest['nodes'].values() if n.get('resource_type') == 'model' and n.get('package_name') == 'sattrack')} models, "
          f"{len(problems)} problem(s)")
    return 1 if problems else 0


def header_description(sql_path: Path) -> str:
    lines = []
    for line in sql_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("--"):
            lines.append(line[2:].strip())
        elif lines:
            break
    return re.sub(r"\s+", " ", " ".join(lines)).replace('"', "'")


def scaffold(con, model: str) -> int:
    sql = next(TRANSFORM.joinpath("models").rglob(f"{model}.sql"), None)
    cols = built_columns(con, model)
    if sql is None or not cols:
        print(f"{model}: needs both a SQL file and a built table (dbt run --select {model} first)", file=sys.stderr)
        return 1
    docs = set(re.findall(r"docs col__(\w+)", REGISTRY.read_text(encoding="utf-8")))
    is_mart = "models/marts/" in sql.as_posix()
    out = [f"  - name: {model}", f"    description: \"{header_description(sql) or 'TODO'}\""]
    if is_mart:
        out += ["    config:", "      access: public"]
    out += ["    data_tests:"]
    for check_name in ("pk_unique", "pk_not_null"):
        out += ["      - model_health:", f"          name: mh__{model}__{check_name}",
                f"          arguments: {{check: {check_name}, columns: [TODO_pk]}}"]
    out += ["      - model_health:", f"          name: mh__{model}__row_count_match",
            "          arguments:", "            check: row_count_match",
            "            compare_to: \"ref('TODO_upstream')\"", "            relationship: equal   # equal | lte | gte",
            "    columns:"]
    for name, dtype in cols:
        out.append(f"      - name: {name}")
        if is_mart:
            out.append(f"        data_type: {dtype}")
        out.append(f"        description: '{{{{ doc(\"col__{name}\") }}}}'" if name in docs
                   else "        description: \"TODO (add a sourced definition to docs/column_definitions.md)\"")
    print("\n".join(out))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--scaffold", metavar="MODEL")
    ap.add_argument("--db", default=str(BUILD_DB))
    ap.add_argument("--manifest", default=str(TRANSFORM / "target" / "manifest.json"))
    args = ap.parse_args()
    with connect(args.db, read_only=True) as con:
        return check(con, Path(args.manifest)) if args.check else scaffold(con, args.scaffold)


if __name__ == "__main__":
    sys.exit(main())
