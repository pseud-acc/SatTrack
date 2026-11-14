"""Bespoke dbt-bouncer checks: data tests (required generic tests, test naming).

Generic: the test names, kwargs and name templates come from the parameters set in dbt-bouncer.yml.
"""
from __future__ import annotations

import re

from dbt_bouncer.check_framework.decorator import check, fail


@check
def check_bespoke_model_has_generic_test(model, ctx, *, test_name: str, kwarg: str, required_values: list[str]):
    """The model has one `test_name` generic test for each required value of `kwarg`
    (e.g. model_health with check: pk_unique and check: pk_not_null)."""
    found = set()
    for t in ctx.tests_by_attached_node.get(model.unique_id, []):
        meta = t.test_metadata
        if meta and meta.name == test_name:
            found.add((meta.kwargs or {}).get(kwarg))
    missing = [v for v in required_values if v not in found]
    if missing:
        fail(f"`{model.name}` has no `{test_name}` test with {kwarg} in {missing}.")


@check
def check_bespoke_test_names(test, *, exact_name_templates: dict[str, str], default_name_pattern: str):
    """Generic test names follow a template.

    exact_name_templates: generic test -> exact name, formatted with {model}, {column} and the test's kwargs
        (e.g. model_health: "mh__{model}__{check}").
    default_name_pattern: regex for every other generic test, formatted with the escaped {model} and an
        optional {column_suffix} (e.g. "^(?!mh__)[a-z][a-z0-9_]*?__{model}{column_suffix}$").
    Singular tests are not covered.
    """
    meta = test.test_metadata
    if not meta or not test.attached_node:
        return
    model = test.attached_node.split(".")[-1]
    kwargs = dict(meta.kwargs or {})
    column = kwargs.get("column_name") or test.column_name
    if meta.name in exact_name_templates:
        # the test's kwargs first: generic tests carry their own `model` kwarg (the relation), which the
        # attached model's name must override
        expected = exact_name_templates[meta.name].format(**{**kwargs, "model": model, "column": column})
        if test.name != expected:
            fail(f"Test `{test.name}` should be named `{expected}`.")
        return
    pattern = default_name_pattern.format(
        model=re.escape(model), column_suffix=f"(__{re.escape(column)})?" if column else "")
    if not re.match(pattern, test.name):
        fail(f"Test `{test.name}` does not match `{pattern}`.")
