"""Tests for bespoke/manifest/bespoke_sources_macros.py and bespoke_tests.py."""
from __future__ import annotations

from conftest import fails, macro, model, passes

# ---------------------------------------------------------------- check_bespoke_source_file_path
TEMPLATE = "models/staging/{source_name}/_{source_name}__sources.yml"


def test_source_file_path_pass():
    passes("check_bespoke_source_file_path", source={"source_name": "gcat", "name": "satcat",
           "original_file_path": "models/staging/gcat/_gcat__sources.yml"}, path_template=TEMPLATE)


def test_source_file_path_pass_windows_separators():
    passes("check_bespoke_source_file_path", source={"source_name": "gcat", "name": "satcat",
           "original_file_path": "models\\staging\\gcat\\_gcat__sources.yml"}, path_template=TEMPLATE)


def test_source_file_path_fail():
    fails("check_bespoke_source_file_path", match="expected `models/staging/gcat/_gcat__sources.yml`",
          source={"source_name": "gcat", "name": "satcat", "original_file_path": "models/staging/_sources.yml"},
          path_template=TEMPLATE)


# ---------------------------------------------------------------- check_bespoke_source_loaded_at_field
def test_source_loaded_at_field_pass():
    passes("check_bespoke_source_loaded_at_field", source={"loaded_at_field": "_loaded_at", "config": {}})


def test_source_loaded_at_query_pass():
    passes("check_bespoke_source_loaded_at_field",
           source={"loaded_at_field": None, "config": {"loaded_at_query": "select max(_loaded_at) from x"}})


def test_source_loaded_at_field_fail():
    fails("check_bespoke_source_loaded_at_field", match="no loaded_at_field",
          source={"loaded_at_field": None, "config": {}})


def test_source_loaded_at_field_fail_no_config():
    fails("check_bespoke_source_loaded_at_field", source={"loaded_at_field": ""})


# ---------------------------------------------------------------- check_bespoke_macro_arguments_documented
SIG = "{% macro helper__m(relation, column_name, sep=',') %}\nselect 1\n{% endmacro %}"
ARGS = [
    {"name": "relation", "type": "relation", "description": "The relation to read."},
    {"name": "column_name", "type": "string", "description": "The column."},
    {"name": "sep", "type": "string", "description": "Separator."},
]


def test_macro_arguments_documented_pass():
    passes("check_bespoke_macro_arguments_documented", macro=macro(macro_sql=SIG, arguments=ARGS))


def test_macro_arguments_documented_pass_no_arguments():
    passes("check_bespoke_macro_arguments_documented",
           macro=macro(macro_sql="{% macro helper__m() %}select 1{% endmacro %}", arguments=[]))


def test_macro_arguments_documented_pass_generic_test_signature():
    code = "{% test model_health(model, check) %}\nselect 1\n{% endtest %}"
    passes("check_bespoke_macro_arguments_documented", macro=macro(name="test_model_health", macro_sql=code,
           arguments=[{"name": "model", "type": "relation", "description": "The model."},
                      {"name": "check", "type": "string", "description": "The check to run."}]))


def test_macro_arguments_documented_fail_undocumented_untyped_short_and_extra():
    args = [
        {"name": "relation", "type": "", "description": "The relation to read."},
        {"name": "column_name", "type": "string", "description": "col"},
        {"name": "old_arg", "type": "string", "description": "No longer in the signature."},
    ]
    fails("check_bespoke_macro_arguments_documented",
          match=r"relation \(no type\).*column_name \(no description\).*sep \(undocumented\).*\['old_arg'\]",
          macro=macro(macro_sql=SIG, arguments=args))


def test_macro_arguments_documented_type_optional():
    args = [{**a, "type": None} for a in ARGS]
    passes("check_bespoke_macro_arguments_documented", macro=macro(macro_sql=SIG, arguments=args), require_type=False)
    fails("check_bespoke_macro_arguments_documented", match="no type", macro=macro(macro_sql=SIG, arguments=args))


# ---------------------------------------------------------------- check_bespoke_one_macro_per_file
def test_one_macro_per_file_pass():
    m = macro(name="helper__a")
    passes("check_bespoke_one_macro_per_file", macro=m, ctx_macros=[m, macro(name="helper__b")])


def test_one_macro_per_file_fail():
    a = macro(name="helper__a", original_file_path="macros/helpers/shared.sql")
    b = macro(name="helper__b", original_file_path="macros/helpers/shared.sql")
    fails("check_bespoke_one_macro_per_file", match=r"defines 2 macros: \['helper__a', 'helper__b'\]",
          macro=a, ctx_macros=[a, b, macro(name="helper__c")])


# ---------------------------------------------------------------- check_bespoke_model_has_generic_test
MH = {"test_name": "model_health", "kwarg": "check", "required_values": ["pk_unique", "pk_not_null"]}


def _mh_test(check: str, attached: str = "model.sattrack.int__a__b", name: str = "model_health") -> dict:
    return {"name": f"mh__x__{check}", "attached_node": attached,
            "test_metadata": {"name": name, "kwargs": {"check": check}}}


def test_has_generic_test_pass():
    passes("check_bespoke_model_has_generic_test", model=model(),
           ctx_tests=[_mh_test("pk_unique"), _mh_test("pk_not_null"), _mh_test("row_count")], **MH)


def test_has_generic_test_fail_one_missing():
    fails("check_bespoke_model_has_generic_test", match=r"in \['pk_not_null'\]", model=model(),
          ctx_tests=[_mh_test("pk_unique")], **MH)


def test_has_generic_test_fail_tests_on_other_model_or_other_generic():
    fails("check_bespoke_model_has_generic_test", match=r"in \['pk_unique', 'pk_not_null'\]", model=model(),
          ctx_tests=[_mh_test("pk_unique", attached="model.sattrack.other"),
                     _mh_test("pk_not_null", name="not_null"),
                     {"name": "singular_test", "attached_node": "model.sattrack.int__a__b", "test_metadata": None}],
          **MH)


# ---------------------------------------------------------------- check_bespoke_test_names
NAMES = {"exact_name_templates": {"model_health": "mh__{model}__{check}"},
         "default_name_pattern": "^(?!mh__)[a-z][a-z0-9_]*?__{model}{column_suffix}$"}


def _test(name: str, generic: str, kwargs: dict | None = None, column: str | None = None,
          attached: str | None = "model.sattrack.int__a__b") -> dict:
    return {"name": name, "attached_node": attached, "column_name": column,
            "test_metadata": {"name": generic, "kwargs": kwargs or {}}}


def test_test_names_exact_template_pass():
    # the generic test's own `model` kwarg (a Jinja relation string) must not override the attached model name
    passes("check_bespoke_test_names", test=_test(
        "mh__int__a__b__pk_unique", "model_health",
        {"check": "pk_unique", "model": "{{ get_where_subquery(ref('int__a__b')) }}"}), **NAMES)


def test_test_names_exact_template_fail():
    fails("check_bespoke_test_names", match="should be named `mh__int__a__b__pk_unique`",
          test=_test("pk_unique__int__a__b", "model_health", {"check": "pk_unique"}), **NAMES)


def test_test_names_default_pattern_pass_model_and_column():
    passes("check_bespoke_test_names", test=_test("accepted_range__int__a__b", "expect_x"), **NAMES)
    passes("check_bespoke_test_names", test=_test("not_null__int__a__b__x_id", "not_null",
           {"column_name": "x_id"}, column="x_id"), **NAMES)
    passes("check_bespoke_test_names", test=_test("not_null__int__a__b", "not_null", column="x_id"), **NAMES)


def test_test_names_default_pattern_fail():
    fails("check_bespoke_test_names", match="does not match",
          test=_test("not_null_int__a__b_x_id", "not_null", column="x_id"), **NAMES)
    fails("check_bespoke_test_names", match="does not match",
          test=_test("not_null__int__a__b__other_col", "not_null", column="x_id"), **NAMES)
    fails("check_bespoke_test_names", match="does not match",
          test=_test("mh__int__a__b", "unique"), **NAMES)  # mh__ is reserved for model_health


def test_test_names_singular_or_unattached_skipped():
    passes("check_bespoke_test_names", test={"name": "Whatever", "attached_node": "model.sattrack.int__a__b",
           "test_metadata": None}, **NAMES)
    passes("check_bespoke_test_names", test=_test("Whatever", "not_null", attached=None), **NAMES)
