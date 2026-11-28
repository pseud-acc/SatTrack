"""Unit tests: app/core/filter_spec.py against the shared conformance cases (tests/contracts/filter_spec_cases.json,
D-034), plus the field labels it exposes. Expected selections are written out by hand in the cases file."""
import copy
import json
import re
from pathlib import Path

import pytest

from app.core import filter_spec

CASES = json.loads((Path(__file__).resolve().parents[1] / "contracts" / "filter_spec_cases.json")
                   .read_text(encoding="utf-8"))


def expand(spec):
    """The cases file's placeholders: clauses "REPEAT_<n>" and values "LONG_<n>"."""
    spec = copy.deepcopy(spec)
    if isinstance(spec, dict) and isinstance(spec.get("clauses"), str):
        n = int(re.fullmatch(r"REPEAT_(\d+)", spec["clauses"]).group(1))
        spec["clauses"] = [{"field": "orbit_class", "op": "eq", "value": "LEO"} for _ in range(n)]
    for clause in spec.get("clauses", []) if isinstance(spec, dict) else []:
        if isinstance(clause.get("value"), str) and (m := re.fullmatch(r"LONG_(\d+)", clause["value"])):
            clause["value"] = "A" * int(m.group(1))
    return spec


@pytest.mark.parametrize("case", CASES["valid"], ids=lambda c: c["name"])
def test_valid_case_selects_expected(case):
    assert filter_spec.select_ids(expand(case["spec"]), CASES["records"]) == case["expected"]


@pytest.mark.parametrize("case", CASES["invalid"], ids=lambda c: c["name"])
def test_invalid_case_is_rejected(case):
    with pytest.raises(filter_spec.InvalidSpec):
        filter_spec.select_ids(expand(case["spec"]), CASES["records"])


def test_error_message_does_not_echo_input():
    with pytest.raises(filter_spec.InvalidSpec) as e:
        filter_spec.validate({"version": 1, "clauses": [{"field": "<script>alert(1)</script>", "op": "eq", "value": 1}]})
    assert "<script>" not in str(e.value)


def test_every_field_has_a_readable_label():
    """Users never see a snake_case name: every allowed field has a label from its dbt meta, with no underscores."""
    fields = filter_spec.fields()
    assert set(fields) == {"satcat_id", "object_name", "object_type", "operational_status", "orbit_class",
                           "owner_country", "launch_vehicle_brand", "mission_category_labels", "launch_year",
                           "satellite_constellation_name", "primary_satellite_system_name",
                           "satellite_system_names"}
    for name, f in fields.items():
        assert f["label"] and "_" not in f["label"] and f["label"] != name
    assert filter_spec.label("mission_category_labels") == "Purpose"


def test_threshold_limits_are_the_documented_ones():
    s = filter_spec.schema()
    assert s["properties"]["clauses"]["maxItems"] == 32
    assert s["properties"]["version"] == {"const": 1}
