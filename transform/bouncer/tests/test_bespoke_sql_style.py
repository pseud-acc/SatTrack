"""Tests for bespoke/manifest/bespoke_sql_style.py: leading commas and explicit joins (models and macros)."""
from __future__ import annotations

from conftest import fails, macro, model, passes, sql

GOOD = sql("""
    with cte_a as (
        select
            a.x_id
            , coalesce(a.name, 'n, a') as name                -- comma in a string and a function call
            , row_number() over (partition by a.x, a.y order by a.z) as rn
            , {{ helper__m('a', 'b') }} as m                   -- commas inside Jinja
        from {{ ref('a') }} as a
        cross join {{ ref('b') }} as b
        where a.x_id in (1, 2, 3)
        group by 1, 2, 3, 4
        order by 1, 2
    )

    , cte_final as (
        select
            x_id
            , name
        from cte_a
    )

    select * from cte_final
""")


# ---------------------------------------------------------------- scan_commas edge cases (model check)
def test_model_leading_commas_pass():
    passes("check_bespoke_model_leading_commas", model=model(raw_code=GOOD))


def test_model_leading_commas_pass_crlf_and_comments():
    code = "/* a, b, c */\n{# x, y #}\n" + GOOD.replace("\n", "\r\n")
    passes("check_bespoke_model_leading_commas", model=model(raw_code=code))


def test_model_leading_commas_fail_trailing_comma():
    code = GOOD.replace("        x_id\n        , name\n    from cte_a", "        x_id,\n        name\n    from cte_a")
    fails("check_bespoke_model_leading_commas", match=r"has 1 list line.*'x_id,'", model=model(raw_code=code))


def test_model_leading_commas_fail_two_items_on_one_line():
    code = GOOD.replace("        x_id\n        , name\n    from cte_a", "        x_id, name\n    from cte_a")
    fails("check_bespoke_model_leading_commas", match="x_id, name", model=model(raw_code=code))


def test_model_leading_commas_fail_paren_comma_between_ctes():
    code = GOOD.replace(")\n\n, cte_final as (", "),\n\ncte_final as (")
    fails("check_bespoke_model_leading_commas", match=r"'\),'", model=model(raw_code=code))


def test_model_leading_commas_fail_in_subquery_select():
    code = GOOD.replace("where a.x_id in (1, 2, 3)", "where a.x_id in (select p, q from t)")
    fails("check_bespoke_model_leading_commas", match="select p, q from t", model=model(raw_code=code))


def test_model_leading_commas_one_report_per_line_and_max_examples():
    code = sql("""
        select a, b, c
            , d, e
            , f, g
        from t
    """)
    fails("check_bespoke_model_leading_commas", match=r"has 3 list line\(s\).*\['select a, b, c', ', d, e'\]",
          model=model(raw_code=code), max_examples=2)


# ---------------------------------------------------------------- check_bespoke_macro_leading_commas
def test_macro_leading_commas_pass():
    code = "{% macro helper__m(a, b) %}\n" + GOOD + "\n{% endmacro %}"
    passes("check_bespoke_macro_leading_commas", macro=macro(macro_sql=code))


def test_macro_leading_commas_fail():
    code = "{% macro helper__m(a, b) %}\nselect\n    x,\n    y\nfrom t\n{% endmacro %}"
    fails("check_bespoke_macro_leading_commas", match=r"Macro `helper__m` has 1 list line", macro=macro(macro_sql=code))


# ---------------------------------------------------------------- check_bespoke_model_explicit_joins
def test_model_explicit_joins_pass():
    passes("check_bespoke_model_explicit_joins", model=model(raw_code=GOOD))


def test_model_explicit_joins_pass_from_list_ends_at_clause():
    # commas after where / group by / order by / using are not comma joins
    code = sql("""
        select
            a.x
        from a
        inner join b using (x, y)
        where a.x in (1, 2)
        group by a.x, a.y
        order by a.x, a.y
    """)
    passes("check_bespoke_model_explicit_joins", model=model(raw_code=code))


def test_model_explicit_joins_pass_function_in_from():
    code = "select\n    u.v\nfrom unnest([1, 2, 3]) as u(v)\n"
    passes("check_bespoke_model_explicit_joins", model=model(raw_code=code))


def test_model_explicit_joins_fail():
    code = "select\n    a.x\n    , b.y\nfrom {{ ref('a') }} as a, {{ ref('b') }} as b\nwhere a.id = b.id\n"
    fails("check_bespoke_model_explicit_joins", match="joins with a comma", model=model(raw_code=code))


def test_model_explicit_joins_fail_leading_comma_join_inside_cte():
    code = GOOD.replace("    cross join {{ ref('b') }} as b", "    , {{ ref('b') }} as b")
    fails("check_bespoke_model_explicit_joins", match="jinja_expr as b", model=model(raw_code=code))


# ---------------------------------------------------------------- check_bespoke_macro_explicit_joins
def test_macro_explicit_joins_pass():
    passes("check_bespoke_macro_explicit_joins",
           macro=macro(macro_sql="{% macro helper__m(rel) %}\nselect\n    a.x\nfrom {{ rel }} as a\n"
                                 "left join b on a.id = b.id\n{% endmacro %}"))


def test_macro_explicit_joins_fail():
    fails("check_bespoke_macro_explicit_joins", match="Macro `helper__m` joins with a comma",
          macro=macro(macro_sql="{% macro helper__m(rel) %}\nselect\n    a.x\nfrom {{ rel }} as a, b\n{% endmacro %}"))


# ---------------------------------------------------------------- surrogate-key naming (SQL-07)
SK_GOOD = sql("""
    select
        {{ dbt_utils.generate_surrogate_key(['a', 'b']) }} as map_sk
        , a
    from cte_x
""")


def test_model_surrogate_key_suffix_pass():
    passes("check_bespoke_model_surrogate_key_suffix", model=model(raw_code=SK_GOOD), suffix="_sk")


def test_model_surrogate_key_suffix_fail():
    code = SK_GOOD.replace("as map_sk", "as map_id")
    fails("check_bespoke_model_surrogate_key_suffix", match=r"\['map_id'\]", model=model(raw_code=code), suffix="_sk")


def test_model_surrogate_key_suffix_ignores_other_macros():
    code = sql("""
        select
            {{ helper__clean(a) }} as a_id
        from cte_x
    """)
    passes("check_bespoke_model_surrogate_key_suffix", model=model(raw_code=code), suffix="_sk")


def test_macro_surrogate_key_suffix_fail():
    code = "{{ dbt_utils.generate_surrogate_key(['entity_key', \"'\" ~ role ~ \"'\", 'ord']) }} as map_id"
    fails("check_bespoke_macro_surrogate_key_suffix", match=r"Macro `helper__m`.*\['map_id'\]",
          macro=macro(macro_sql=code), suffix="_sk")


def test_macro_surrogate_key_suffix_pass():
    code = "{{ dbt_utils.generate_surrogate_key(['entity_key', 'ord']) }} as map_sk"
    passes("check_bespoke_macro_surrogate_key_suffix", macro=macro(macro_sql=code), suffix="_sk")


def test_column_suffix_not_allowed_fail():
    fails("check_bespoke_model_column_suffix_not_allowed", match=r"\['country_key'\]",
          model=model(columns={"country_key": {}, "name_key": {}, "country_sk": {}}),
          suffixes=["_key"], allowed_columns=["name_key"])


def test_column_suffix_not_allowed_pass_with_exception():
    passes("check_bespoke_model_column_suffix_not_allowed",
           model=model(columns={"name_key": {}, "country_sk": {}}), suffixes=["_key"], allowed_columns=["name_key"])
