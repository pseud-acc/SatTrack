"""The browser's filter spec (static/viewer/filter_spec.js, roadmap 3.3a) against the shared conformance cases
(tests/contracts/filter_spec_cases.json, D-034), in headless Chromium: every valid case selects exactly its hand-worked
ids, in record order, and every invalid spec is rejected. The rules come from the server's browser_rules() (generated
from the schema), as the viewer config carries them. Placeholders are expanded as in tests/app/test_filter_spec.py.
The file needs no viewer flag and no Cesium, and must import nothing."""
import copy
import json
import re
from pathlib import Path

import pytest

from app.core.filter_spec import browser_rules

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests" / "contracts" / "filter_spec_cases.json").read_text(encoding="utf-8"))
MODULE = ROOT / "static" / "viewer" / "filter_spec.js"


def expand(spec):
    """The cases file's placeholders: clauses "REPEAT_<n>" and values "LONG_<n>" (as tests/app/test_filter_spec.py)."""
    spec = copy.deepcopy(spec)
    if isinstance(spec, dict) and isinstance(spec.get("clauses"), str):
        n = int(re.fullmatch(r"REPEAT_(\d+)", spec["clauses"]).group(1))
        spec["clauses"] = [{"field": "orbit_class", "op": "eq", "value": "LEO"} for _ in range(n)]
    for clause in spec.get("clauses", []) if isinstance(spec, dict) else []:
        if isinstance(clause.get("value"), str) and (m := re.fullmatch(r"LONG_(\d+)", clause["value"])):
            clause["value"] = "A" * int(m.group(1))
    return spec


RUN = """async ([url, rules, records, specs]) => {
    const m = await import(url);
    return specs.map((spec) => {
        try { return {ok: true, ids: m.selectIds(spec, records, rules)}; }
        catch (e) { return {ok: false, invalid: e instanceof m.InvalidSpec, error: String(e)}; }
    });
}"""


@pytest.fixture(scope="module")
def results(browser, base_url):
    """Run every case in one page: {("valid"|"invalid", index): result}."""
    page = browser.new_page()
    page.goto(base_url + "/static/viewer/filter_spec.js")
    url = base_url + "/static/viewer/filter_spec.js"
    valid = [expand(c["spec"]) for c in CASES["valid"]]
    invalid = [expand(c["spec"]) for c in CASES["invalid"]]
    out = page.evaluate(RUN, [url, browser_rules(), CASES["records"], valid + invalid])
    page.close()
    return {**{("valid", i): r for i, r in enumerate(out[:len(valid)])},
            **{("invalid", i): r for i, r in enumerate(out[len(valid):])}}


@pytest.mark.parametrize("i", range(len(CASES["valid"])), ids=[c["name"] for c in CASES["valid"]])
def test_valid_case_selects_the_expected_ids(results, i):
    r = results[("valid", i)]
    assert r["ok"], r.get("error")
    assert r["ids"] == CASES["valid"][i]["expected"]


@pytest.mark.parametrize("i", range(len(CASES["invalid"])), ids=[c["name"] for c in CASES["invalid"]])
def test_invalid_case_is_rejected(results, i):
    r = results[("invalid", i)]
    assert not r["ok"] and r["invalid"], r


def test_module_imports_nothing_and_never_evaluates_code():
    text = MODULE.read_text(encoding="utf-8")
    code = re.sub(r"//.*", "", text)
    assert not re.search(r"^\s*import\b|\bimport\(", code, flags=re.M)
    assert "eval(" not in code and "new Function" not in code


def test_browser_rules_follow_the_schema():
    """The rules the browser validates against are the generated schema's, field for field and operator for operator."""
    schema = json.loads((ROOT / "app" / "contracts" / "filter_spec.schema.json").read_text(encoding="utf-8"))
    rules = browser_rules()
    assert rules["version"] == schema["properties"]["version"]["const"]
    assert rules["maxClauses"] == schema["properties"]["clauses"]["maxItems"]
    assert list(rules["fields"]) == list(schema["$defs"])
    for name, d in schema["$defs"].items():
        assert rules["fields"][name]["kind"] == d["x-kind"]
        assert rules["fields"][name]["ops"] == {b["properties"]["op"]["const"]: b["properties"]["value"]
                                                for b in d["oneOf"]}
