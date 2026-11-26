"""The filter spec (roadmap 2.2; D-030 to D-034): validate a spec and apply it to a table of objects.

A spec selects objects: {"version": 1, "clauses": [{"field", "op", "value"}, ...]}, every clause must hold (AND).
Field names are the `objects` dataset's own; app/contracts/filter_spec.schema.json lists the allowed fields, their
operators and value types, and each field's label. The browser applies the same spec in Phase 3; both
implementations run the shared cases in tests/contracts/filter_spec_cases.json.

Missing values are explicit (D-032). A scalar is missing when it is null; a list field when it is null or empty.
  eq            value == v; never matches a missing value
  in            value is one of the list; null in the list matches a missing value
  not_in        the exact complement of `in` with the same list: missing matches unless null is listed
  between       min <= value <= max (inclusive); missing matches only with "include_missing": true
  contains_any  the list field shares an element with the values; null in the values matches a missing list
  is_missing    true: only missing values; false: only present ones
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import jsonschema
import pandas as pd

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "contracts" / "filter_spec.schema.json"


class InvalidSpec(ValueError):
    """The spec breaks the schema. The message names the clause, never echoes long user input."""


@lru_cache(maxsize=1)
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _validator():
    return jsonschema.Draft202012Validator(schema())


def fields() -> dict[str, dict]:
    """{field: {"label", "kind", "values"}} for every allowed field, in the schema's order."""
    return {name: {"label": d["title"], "kind": d["x-kind"], "values": d.get("x-values")}
            for name, d in schema()["$defs"].items()}


@lru_cache(maxsize=1)
def browser_rules() -> dict:
    """What the browser's implementation (static/viewer/filter_spec.js) validates against, taken from the generated
    schema so nothing is copied by hand: the version, the clause limit and, per field, its kind and the JSON Schema of
    each operator's value. Sent in the viewer config (roadmap 3.3a)."""
    s = schema()
    return {
        "version": s["properties"]["version"]["const"],
        "maxClauses": s["properties"]["clauses"]["maxItems"],
        "fields": {name: {"kind": d["x-kind"],
                          "ops": {b["properties"]["op"]["const"]: b["properties"]["value"] for b in d["oneOf"]}}
                   for name, d in s["$defs"].items()},
    }


def label(field: str) -> str:
    """The label people see for a field (from its dbt `meta.label`)."""
    return fields()[field]["label"]


def validate(spec) -> dict:
    """Return the spec if it matches the schema, else raise InvalidSpec."""
    errors = sorted(_validator().iter_errors(spec), key=lambda e: list(e.absolute_path))
    if errors:
        where = "/".join(str(p) for p in errors[0].absolute_path) or "spec"
        raise InvalidSpec(f"invalid filter spec at {where}")
    return spec


def _missing_scalar(s: pd.Series) -> pd.Series:
    return s.isna()


def _missing_list(s: pd.Series) -> pd.Series:
    return s.map(lambda v: v is None or (isinstance(v, float) and math.isnan(v)) or len(v) == 0).astype(bool)


def _clause_mask(df: pd.DataFrame, clause: dict, kind: str) -> pd.Series:
    col, op, value = df[clause["field"]], clause["op"], clause["value"]
    if kind == "string_list":
        missing = _missing_list(col)
        if op == "is_missing":
            return missing if value else ~missing
        wanted = {v for v in value if v is not None}
        hit = col.map(lambda v: v is not None and not (isinstance(v, float)) and bool(wanted.intersection(v)))
        return hit.astype(bool) | (missing if None in value else False)
    missing = _missing_scalar(col)
    if op == "is_missing":
        return missing if value else ~missing
    if op == "eq":
        return (col == value) & ~missing
    if op in ("in", "not_in"):
        present = [v for v in value if v is not None]
        inside = (col.isin(present) & ~missing) | (missing & (None in value))
        return inside if op == "in" else ~inside
    if op == "between":
        within = (col >= value["min"]) & (col <= value["max"]) & ~missing
        return within | (missing & bool(value.get("include_missing", False)))
    raise InvalidSpec(f"unknown op {op}")   # unreachable after validate()


def apply(spec: dict, df: pd.DataFrame) -> pd.Series:
    """Boolean mask over df's rows: True where every clause holds. df has one column per field used, named as in
    the spec. Validates the spec first."""
    validate(spec)
    kinds = {name: f["kind"] for name, f in fields().items()}
    mask = pd.Series(True, index=df.index)
    for clause in spec["clauses"]:
        mask &= _clause_mask(df, clause, kinds[clause["field"]])
    return mask


class MissingObjectsDataset(RuntimeError):
    """The app can't filter without the objects dataset (D-035): start-up fails loudly instead of falling back."""


def table_from_records(records: list[dict], key: str = "satcat_id") -> pd.DataFrame:
    """The filter table: one row per object, with the key and every filterable field."""
    return pd.DataFrame.from_records(records, columns=list(dict.fromkeys([key, *fields()])))


def table_from_dataset(dataset: dict | None) -> pd.DataFrame:
    """Build the filter table from the objects dataset as the app holds it ({encoding: {"body", "sha256"}}), using
    the gzip copy. Checks the envelope's name and count. Raises MissingObjectsDataset if it's absent or unusable.
    Measured on the full 21 Nov export (D-035): 0.86 s, ~81 MB peak, ~15 MB kept per worker."""
    import gzip
    if not dataset or "gzip" not in dataset:
        raise MissingObjectsDataset(
            "objects dataset missing: the app filters satellites with it (D-035). The pipeline publishes "
            "objects.json.gz/.br with the CSVs (app/current.json on S3, or the SATTRACK_APP_DATA_DIR folder).")
    try:
        doc = json.loads(gzip.decompress(dataset["gzip"]["body"]))
    except Exception as exc:   # corrupt file: name the type only
        raise MissingObjectsDataset(f"objects dataset unreadable ({type(exc).__name__})") from None
    if doc.get("dataset") != "objects" or doc.get("count") != len(doc.get("records") or []):
        raise MissingObjectsDataset("objects dataset failed its envelope check (dataset name or count)")
    table = table_from_records(doc["records"])
    del doc
    return table


def select_ids(spec: dict, records: list[dict], key: str = "satcat_id") -> list:
    """The keys of the records the spec selects, in record order: the shape the conformance cases check."""
    df = table_from_records(records, key)
    return df.loc[apply(spec, df), key].tolist()
