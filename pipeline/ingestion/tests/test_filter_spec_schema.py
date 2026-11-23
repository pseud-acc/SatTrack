"""Tests: scripts/build_filter_spec_schema.py (D-033). The committed app/contracts/filter_spec.schema.json must match
a fresh build from app/contracts/filter_fields.yml and the dbt mart YAML (this is the CI sync check), every
filterable field must have a label, and the shared conformance cases must agree with the schema."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import jsonschema
import pytest

PIPELINE = Path(__file__).resolve().parents[2]
REPO = PIPELINE.parent
_spec = importlib.util.spec_from_file_location("build_filter_spec_schema",
                                               PIPELINE / "scripts" / "build_filter_spec_schema.py")
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)


def test_committed_schema_is_up_to_date():
    assert b.main(["--check"]) == 0, "run: python pipeline/scripts/build_filter_spec_schema.py"


def test_every_filterable_field_has_a_label_from_dbt_meta():
    schema = b.build()
    for name, field in schema["$defs"].items():
        assert field["title"] and "_" not in field["title"], name


def write(tmp_path, columns_yaml, fields_yaml):
    marts = tmp_path / "marts"
    marts.mkdir()
    (marts / "_m.yml").write_text("models:\n  - name: fct__m\n    columns:\n" + columns_yaml, encoding="utf-8")
    fields = tmp_path / "fields.yml"
    fields.write_text(fields_yaml, encoding="utf-8")
    return fields, marts


LABELLED = ("      - name: a\n        data_type: varchar\n        config:\n          meta:\n            label: \"A thing\"\n"
            "        data_tests:\n          - accepted_values:\n              name: av\n"
            "              arguments: {values: [\"x\", \"y\"]}\n")


def test_types_values_and_labels_come_from_the_yaml(tmp_path):
    fields, marts = write(tmp_path, LABELLED, "fields:\n  - name: a\n    model: fct__m\n")
    d = b.build(fields, marts)["$defs"]["a"]
    assert d["title"] == "A thing" and d["x-kind"] == "string" and d["x-values"] == ["x", "y"]
    assert [v["properties"]["op"]["const"] for v in d["oneOf"]] == ["eq", "in", "not_in", "is_missing"]


@pytest.mark.parametrize("columns, message", [
    ("      - name: a\n        data_type: varchar\n", "no `config: meta: label:`"),
    ("      - name: a\n        data_type: varchar\n        config:\n          meta:\n            label: \" \"\n",
     "no `config: meta: label:`"),
    ("      - name: b\n        data_type: varchar\n", "no column a"),
    ("      - name: a\n        data_type: timestamp\n        config:\n          meta:\n            label: \"A\"\n",
     "has no filter rules"),
])
def test_build_fails_without_a_label_column_or_known_type(tmp_path, columns, message):
    fields, marts = write(tmp_path, columns, "fields:\n  - name: a\n    model: fct__m\n")
    with pytest.raises(b.BuildError, match=re.escape(message)):
        b.build(fields, marts)


def test_a_field_listed_twice_fails(tmp_path):
    fields, marts = write(tmp_path, LABELLED, "fields:\n  - {name: a, model: fct__m}\n  - {name: a, model: fct__m}\n")
    with pytest.raises(b.BuildError, match="twice"):
        b.build(fields, marts)


def test_conformance_cases_agree_with_the_schema():
    """The shared cases' valid specs pass the generated schema and the invalid ones fail it, so the cases stay
    meaningful for the browser implementation too."""
    cases = json.loads((REPO / "tests" / "contracts" / "filter_spec_cases.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(b.build())

    def expand(spec):
        spec = json.loads(json.dumps(spec))
        if isinstance(spec, dict) and isinstance(spec.get("clauses"), str):
            spec["clauses"] = [{"field": "orbit_class", "op": "eq", "value": "LEO"}] * int(spec["clauses"][7:])
        for c in spec.get("clauses", []) if isinstance(spec, dict) else []:
            if isinstance(c.get("value"), str) and c["value"].startswith("LONG_"):
                c["value"] = "A" * int(c["value"][5:])
        return spec

    for case in cases["valid"]:
        assert validator.is_valid(expand(case["spec"])), case["name"]
    for case in cases["invalid"]:
        assert not validator.is_valid(expand(case["spec"])), case["name"]
