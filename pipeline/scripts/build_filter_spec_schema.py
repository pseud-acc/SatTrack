"""Build app/contracts/filter_spec.schema.json from the hand-picked field list and the dbt mart schema YAML (D-033).

    python pipeline/scripts/build_filter_spec_schema.py           write the schema
    python pipeline/scripts/build_filter_spec_schema.py --check   exit 1 if the committed schema is out of date

The field list (app/contracts/filter_fields.yml) says which fields are filterable and which mart documents each.
For every field the column's dbt YAML gives the type (`data_type`), the allowed values (an `accepted_values` test,
when there is one) and the label people see (`config: meta: label:`). A field without a label, a column that
doesn't exist or a type with no filter rules stops the build: users must never see a raw field name.

The spec (D-031): {"version": 1, "clauses": [{"field", "op", "value"}, ...]}, clauses AND-ed. Missing values are
explicit (D-032): `in`/`not_in`/`contains_any` may list null, `between` has `include_missing`, `is_missing` tests
for a missing value directly. Needs PyYAML only (the bouncer and pipeline environments have it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
FIELDS = REPO / "app" / "contracts" / "filter_fields.yml"
MARTS = REPO / "pipeline" / "transform" / "models" / "marts"
OUT = REPO / "app" / "contracts" / "filter_spec.schema.json"

MAX_CLAUSES = 32         # a sidebar uses at most 9; room for NL query without unbounded specs
MAX_VALUES = 1000        # values in one in/not_in/contains_any list
MAX_STRING = 200

# dbt data_type -> filter kind; the kind decides the operators and the JSON type of values
KINDS = {"integer": "integer", "bigint": "integer", "varchar": "string", "varchar[]": "string_list"}
OPS = {
    "integer": ["eq", "in", "not_in", "between", "is_missing"],
    "string": ["eq", "in", "not_in", "is_missing"],
    "string_list": ["contains_any", "is_missing"],
}


class BuildError(Exception):
    pass


def mart_columns(marts_dir: Path = MARTS) -> dict[str, dict[str, dict]]:
    """{model: {column: column YAML}} for every model in the marts' schema YAML."""
    out: dict[str, dict[str, dict]] = {}
    for path in sorted(marts_dir.rglob("*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for model in doc.get("models") or []:
            out[model["name"]] = {c["name"]: c for c in model.get("columns") or []}
    return out


def accepted_values(column: dict) -> list | None:
    for test in column.get("data_tests") or []:
        if isinstance(test, dict) and "accepted_values" in test:
            spec = test["accepted_values"]
            return list((spec.get("arguments") or spec).get("values"))
    return None


def scalar_schema(kind: str, enum: list | None) -> dict:
    if enum is not None:
        return {"enum": enum}
    if kind == "integer":
        return {"type": "integer"}
    return {"type": "string", "minLength": 1, "maxLength": MAX_STRING}


def value_schema(kind: str, op: str, enum: list | None) -> dict:
    one = scalar_schema(kind, enum)
    if op == "eq":
        return one
    if op in ("in", "not_in", "contains_any"):
        return {"type": "array", "minItems": 1, "maxItems": MAX_VALUES, "uniqueItems": True,
                "items": {"anyOf": [one, {"type": "null"}]}}
    if op == "between":
        return {"type": "object", "additionalProperties": False, "required": ["min", "max"],
                "properties": {"min": one, "max": one, "include_missing": {"type": "boolean", "default": False}}}
    if op == "is_missing":
        return {"type": "boolean"}
    raise BuildError(f"no value rule for op {op}")


def field_schema(name: str, model: str, columns: dict) -> dict:
    col = (columns.get(model) or {}).get(name)
    if col is None:
        raise BuildError(f"{name}: no column {name} in {model}'s schema YAML")
    label = ((col.get("config") or {}).get("meta") or {}).get("label")
    if not isinstance(label, str) or not label.strip():
        raise BuildError(f"{name}: {model}.{name} has no `config: meta: label:` in its schema YAML")
    kind = KINDS.get(str(col.get("data_type", "")).lower())
    if kind is None:
        raise BuildError(f"{name}: data_type {col.get('data_type')!r} has no filter rules")
    enum = accepted_values(col)
    variants = [{"type": "object", "additionalProperties": False, "required": ["field", "op", "value"],
                 "properties": {"field": {"const": name}, "op": {"const": op},
                                "value": value_schema(kind, op, enum)}}
                for op in OPS[kind]]
    out = {"title": label.strip(), "x-kind": kind, "x-source": f"{model}.{name}", "oneOf": variants}
    if enum is not None:
        out["x-values"] = enum
    return out


def build(fields_path: Path = FIELDS, marts_dir: Path = MARTS) -> dict:
    listed = (yaml.safe_load(fields_path.read_text(encoding="utf-8")) or {}).get("fields") or []
    if not listed:
        raise BuildError(f"{fields_path}: no fields")
    names = [f["name"] for f in listed]
    if len(names) != len(set(names)):
        raise BuildError("a field is listed twice")
    columns = mart_columns(marts_dir)
    defs = {f["name"]: field_schema(f["name"], f["model"], columns) for f in listed}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://www.sattrackapp.com/contracts/filter_spec.schema.json",
        "title": "SatTrack filter spec",
        "description": ("A selection of objects: clauses AND-ed together, each {field, op, value} on an allowed "
                        "field (D-030 to D-034). Generated by pipeline/scripts/build_filter_spec_schema.py from "
                        "app/contracts/filter_fields.yml and the dbt mart schema YAML; do not edit by hand."),
        "type": "object",
        "additionalProperties": False,
        "required": ["version", "clauses"],
        "properties": {
            "version": {"const": 1},
            "clauses": {"type": "array", "maxItems": MAX_CLAUSES,
                        "items": {"oneOf": [{"$ref": f"#/$defs/{n}"} for n in names]}},
        },
        "$defs": defs,
    }


def render(schema: dict) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the committed schema is out of date")
    args = parser.parse_args(argv)
    try:
        text = render(build())
    except BuildError as e:
        print(f"filter spec schema: {e}", file=sys.stderr)
        return 1
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current.replace("\r\n", "\n") != text:
            print(f"{OUT.relative_to(REPO)} is out of date: run python pipeline/scripts/build_filter_spec_schema.py",
                  file=sys.stderr)
            return 1
        print("filter spec schema is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)} ({len(build()['$defs'])} fields)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
