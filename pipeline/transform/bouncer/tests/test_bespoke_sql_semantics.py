"""Tests for bespoke/manifest/bespoke_sql_semantics.py: sqlglot-based checks on the raw SQL with Jinja
replaced by placeholders (ref -> model name, source -> s__t, macro call -> macro_name())."""
from __future__ import annotations

from conftest import fails, model, passes, sql

# kept indented (not dedented) so the edits below can quote its lines verbatim
MART = """
    {{ config(materialized='table') }}

    with cte_int__a__sat as (
        select
            norad_id
            , object_name
            , launch_date
        from {{ ref('int__a__sat') }}
    )

    , cte_int__a__owner as (
        select
            norad_id
            , owner_code
        from {{ ref('int__a__owner') }}
    )

    , cte_joined as (
        select
            s.norad_id
            , s.object_name
            , s.launch_date
            , coalesce(o.owner_code, 'UNK') as owner_code
            , coalesce(o.owner_code, cast([] as varchar[])) as owner_codes
            , s.norad_id || '-' || o.owner_code as combo_key
            , {{ helper__audit_fields() }}
        from cte_int__a__sat as s
        left join cte_int__a__owner as o
            on s.norad_id = o.norad_id
    )

    , cte_final as (
        select
            cast(norad_id as integer) as norad_id
            , cast(object_name as varchar) as object_name
            , cast(launch_date as date) as launch_date
            , cast(owner_code as varchar) as owner_code
            , cast(owner_codes as varchar[]) as owner_codes
            , cast(combo_key as varchar) as combo_key
            , {{ helper__audit_fields() }}
        from cte_joined
    )

    select * from cte_final
""".strip("\n")

ASSEMBLY = {"allowed_macros": ["helper__audit_fields"]}


def _swap(old: str, new: str) -> str:
    assert old in MART, old
    return MART.replace(old, new)


# ---------------------------------------------------------------- check_bespoke_model_assembly_only
def test_assembly_only_pass_join_default_cast_and_two_relation_logic():
    passes("check_bespoke_model_assembly_only", model=model("fct__x", MART), **ASSEMBLY)


def test_assembly_only_pass_single_macro_body():
    passes("check_bespoke_model_assembly_only", model=model("fct__x", "{{ helper__build_mart('x') }}"), **ASSEMBLY)


def test_assembly_only_fail_logic_from_one_relation():
    code = _swap("            , s.launch_date\n            , coalesce",
                 "            , upper(s.launch_date) as launch_date\n            , coalesce")
    fails("check_bespoke_model_assembly_only", match=r"cte_joined.launch_date: logic reads only \['cte_int__a__sat'\]",
          model=model("fct__x", code), **ASSEMBLY)


def test_assembly_only_fail_default_with_non_constant():
    code = _swap("coalesce(o.owner_code, 'UNK')", "coalesce(o.owner_code, upper(o.owner_code))")
    fails("check_bespoke_model_assembly_only", match="cte_joined.owner_code: logic reads only",
          model=model("fct__x", code), **ASSEMBLY)


def test_assembly_only_fail_default_function_not_allowed():
    code = _swap("coalesce(o.owner_code, 'UNK')", "greatest(o.owner_code, 'UNK')")
    fails("check_bespoke_model_assembly_only", match="cte_joined.owner_code", model=model("fct__x", code), **ASSEMBLY)
    passes("check_bespoke_model_assembly_only", model=model("fct__x", code),
           default_functions=["coalesce", "greatest"], **ASSEMBLY)


def test_assembly_only_fail_unqualified_columns_with_two_relations():
    code = _swap("s.norad_id || '-' || o.owner_code", "norad_id || '-' || owner_code")
    fails("check_bespoke_model_assembly_only", match="cte_joined.combo_key: qualify the columns",
          model=model("fct__x", code), **ASSEMBLY)


def test_assembly_only_unqualified_columns_ok_with_one_relation_but_still_single_source_logic():
    code = MART.replace(", cte_final as (", sql("""
        , cte_extra as (
            select
                norad_id
                , lower(object_name) as object_name_lc
            from cte_joined
        )
    """) + "\n\n    , cte_final as (").replace("from cte_joined\n    )\n\n    select", "from cte_extra\n    )\n\n    select")
    fails("check_bespoke_model_assembly_only", match=r"cte_extra.object_name_lc: logic reads only \['cte_joined'\]",
          model=model("fct__x", code), **ASSEMBLY)


def test_assembly_only_macro_not_allowed():
    fails("check_bespoke_model_assembly_only", match="cte_joined.helper__audit_fields",
          model=model("fct__x", MART), allowed_macros=[])


def test_assembly_only_import_and_final_ctes_exempt():
    # logic inside the import CTE (one relation) and in cte_final (casts) is not this check's business
    code = _swap("            , object_name\n            , launch_date\n        from {{ ref('int__a__sat') }}",
                 "            , upper(object_name) as object_name\n            , launch_date\n"
                 "        from {{ ref('int__a__sat') }}")
    passes("check_bespoke_model_assembly_only", model=model("fct__x", code), **ASSEMBLY)


def test_assembly_only_unparseable_sql_fails_cleanly():
    fails("check_bespoke_model_assembly_only", match="sqlglot could not parse",
          model=model("fct__x", "with cte_final as (select from from where) select * from cte_final"), **ASSEMBLY)


# ---------------------------------------------------------------- check_bespoke_model_final_casts
def test_final_casts_pass():
    passes("check_bespoke_model_final_casts", model=model("fct__x", MART), **ASSEMBLY)


def test_final_casts_fail_bare_column():
    code = _swap("cast(object_name as varchar) as object_name", "object_name")
    fails("check_bespoke_model_final_casts", match=r"object_name \(not a cast of a column\)",
          model=model("fct__x", code), **ASSEMBLY)


def test_final_casts_fail_cast_of_expression():
    code = _swap("cast(object_name as varchar) as object_name", "cast(upper(object_name) as varchar) as object_name")
    fails("check_bespoke_model_final_casts", match=r"object_name \(not a cast of a column\)",
          model=model("fct__x", code), **ASSEMBLY)


def test_final_casts_fail_rename_in_cast():
    code = _swap("cast(object_name as varchar) as object_name", "cast(object_name as varchar) as sat_name")
    fails("check_bespoke_model_final_casts", match=r"sat_name \(casts `object_name` under a new name",
          model=model("fct__x", code), **ASSEMBLY)


def test_final_casts_pass_double_colon_cast():
    code = _swap("cast(object_name as varchar) as object_name", "object_name::varchar as object_name")
    passes("check_bespoke_model_final_casts", model=model("fct__x", code), **ASSEMBLY)


def test_final_casts_fail_macro_not_allowed():
    fails("check_bespoke_model_final_casts", match=r"helper__audit_fields \(not a cast",
          model=model("fct__x", MART), allowed_macros=[])


def test_final_casts_fail_no_final_cte():
    fails("check_bespoke_model_final_casts", match="has no `cte_final` CTE",
          model=model("fct__x", MART.replace("cte_final", "cte_last")), **ASSEMBLY)


# ---------------------------------------------------------------- check_bespoke_model_select_targets_allowed
STAGING = sql("""
    with cte_final as (
        select
            cast(nullif(trim("#JCAT"), '-') as varchar) as jcat
            , cast("Satcat" as integer) as norad_id
            , {{ helper__clean_gcat_text('"Name"') }} as object_name
            , {{ helper__cast_gcat_value('"Mass"', 'double') }} as mass_kg
            , 'gcat' as source_name
            , null as placeholder
            , "Piece" as piece
        from {{ source('gcat', 'satcat') }}
        where "Satcat" is not null
    )

    select * from cte_final
""")
STAGING_ALLOWED = {"allowed_functions": ["nullif", "trim"],
                   "allowed_macros": ["helper__clean_gcat_text", "helper__cast_gcat_value"]}


def test_select_targets_allowed_pass():
    passes("check_bespoke_model_select_targets_allowed", model=model("stg__gcat__satcat", STAGING), **STAGING_ALLOWED)


def test_select_targets_allowed_where_clause_not_checked():
    code = STAGING.replace('where "Satcat" is not null', "where upper(\"Satcat\") like 'X%' and 1 + 1 = 2")
    passes("check_bespoke_model_select_targets_allowed", model=model("stg__gcat__satcat", code), **STAGING_ALLOWED)


def test_select_targets_allowed_fail_function():
    code = STAGING.replace('cast("Satcat" as integer)', 'cast(upper("Satcat") as integer)')
    fails("check_bespoke_model_select_targets_allowed", match=r"norad_id uses \['upper'\]",
          model=model("stg__gcat__satcat", code), **STAGING_ALLOWED)


def test_select_targets_allowed_fail_case_arithmetic_window_subquery():
    code = STAGING.replace('"Piece" as piece', sql("""
        "Piece" as piece
                , case when "Piece" = 'A' then 1 else 0 end as is_a
                , "Mass" * 2 as double_mass
                , row_number() over (order by "Satcat") as rn
                , (select max(x) from t) as sub
    """))
    fails("check_bespoke_model_select_targets_allowed",
          match=r"is_a uses \['case'.*double_mass uses \['mul'\].*rn uses .*'window'.*sub uses .*'subquery'",
          model=model("stg__gcat__satcat", code), **STAGING_ALLOWED)


def test_select_targets_allowed_fail_unlisted_macro():
    code = STAGING.replace("helper__clean_gcat_text", "helper__other")
    fails("check_bespoke_model_select_targets_allowed", match=r"object_name uses \['helper__other'\]",
          model=model("stg__gcat__satcat", code), **STAGING_ALLOWED)


def test_select_targets_allowed_dotted_column_is_not_logic():
    code = STAGING.replace('"Piece" as piece', 's."Piece" as piece').replace(
        "from {{ source('gcat', 'satcat') }}", "from {{ source('gcat', 'satcat') }} as s")
    passes("check_bespoke_model_select_targets_allowed", model=model("stg__gcat__satcat", code), **STAGING_ALLOWED)


# ---------------------------------------------------------------- check_bespoke_model_no_unused_ctes
def test_no_unused_ctes_pass():
    passes("check_bespoke_model_no_unused_ctes", model=model("fct__x", MART))


def test_no_unused_ctes_fail():
    code = _swap("    , cte_final as (", "    , cte_orphan as (\n        select 1 as one\n    )\n\n    , cte_final as (")
    fails("check_bespoke_model_no_unused_ctes", match=r"\['cte_orphan'\]", model=model("fct__x", code))


def test_no_unused_ctes_cte_read_only_in_subquery_counts_as_read():
    code = _swap("    , cte_final as (", "    , cte_lookup as (\n        select 1 as norad_id\n    )\n\n    , cte_final as (")
    code = code.replace("from cte_joined\n    )", "from cte_joined\n        where norad_id in (select norad_id from cte_lookup)\n    )")
    passes("check_bespoke_model_no_unused_ctes", model=model("fct__x", code))


def test_no_unused_ctes_cte_passed_to_macro_counts_as_read():
    code = sql("""
        with cte_int__a__sat as (
            select
                norad_id
            from {{ ref('int__a__sat') }}
        )

        , cte_exploded as (
            {{ helper__explode_org_codes('cte_int__a__sat', 'owner_code') }}
        )

        , cte_final as (
            select
                norad_id
            from cte_exploded
        )

        select * from cte_final
    """)
    passes("check_bespoke_model_no_unused_ctes", model=model("int__x", code))


def test_no_unused_ctes_mention_in_jinja_comment_does_not_count():
    code = _swap("    , cte_final as (", "    , cte_orphan as (\n        select 1 as one\n    )\n\n    , cte_final as (")
    fails("check_bespoke_model_no_unused_ctes", match="cte_orphan",
          model=model("fct__x", "{# reads cte_orphan #}\n" + code))


# ---------------------------------------------------------------- check_bespoke_model_no_subqueries_in_from
def test_no_subqueries_in_from_pass_subquery_in_where_is_fine():
    code = MART.replace("from cte_joined\n    )", "from cte_joined\n        where norad_id in (select norad_id from cte_int__a__sat)\n    )")
    passes("check_bespoke_model_no_subqueries_in_from", model=model("fct__x", code))


def test_no_subqueries_in_from_fail_from():
    code = MART.replace("from cte_joined\n    )", "from (select * from cte_joined) as j\n    )")
    fails("check_bespoke_model_no_subqueries_in_from", match=r"\['j'\]", model=model("fct__x", code))


def test_no_subqueries_in_from_fail_join():
    code = _swap("left join cte_int__a__owner as o",
                        "left join (select norad_id, owner_code from cte_int__a__owner) as o")
    fails("check_bespoke_model_no_subqueries_in_from", match=r"\['o'\]", model=model("fct__x", code))


def test_no_subqueries_in_from_unaliased_subquery_reported():
    code = MART.replace("from cte_joined\n    )", "from (select * from cte_joined)\n    )")
    fails("check_bespoke_model_no_subqueries_in_from", match="SELECT", model=model("fct__x", code))


# ---------------------------------------------------------------- Jinja placeholder handling (all sqlglot checks)
def test_jinja_blocks_and_comments_are_removed():
    code = "{% set cols = ['a', 'b'] %}\n{# a comment with ) unbalanced ( #}\n" + MART.replace(
        "        from cte_joined\n", "        from cte_joined\n        {% if is_incremental() %}where 1 = 1{% endif %}\n")
    for name in ("check_bespoke_model_assembly_only", "check_bespoke_model_final_casts",
                 "check_bespoke_model_no_unused_ctes", "check_bespoke_model_no_subqueries_in_from"):
        passes(name, model=model("fct__x", code), **(ASSEMBLY if "unused" not in name and "subq" not in name else {}))


def test_jinja_var_and_package_macro_placeholders():
    # {{ var(...) }} -> var(); {{ dbt_utils.x(...) }} -> x(); bare {{ expr }} -> null
    code = STAGING.replace("'gcat' as source_name", "{{ var('src') }} as source_name").replace(
        "null as placeholder", "{{ some_value }} as placeholder")
    passes("check_bespoke_model_select_targets_allowed", model=model("stg__gcat__satcat", code),
           allowed_functions=["nullif", "trim"],
           allowed_macros=["helper__clean_gcat_text", "helper__cast_gcat_value", "var"])
    code2 = STAGING.replace("helper__clean_gcat_text(", "dbt_utils.helper__clean_gcat_text(")
    passes("check_bespoke_model_select_targets_allowed", model=model("stg__gcat__satcat", code2), **STAGING_ALLOWED)


def test_in_file_config_call_is_ignored():
    # regression: `{{ config(...) }}` renders to nothing in dbt; it used to become `config()` and fail to parse
    assert MART.lstrip().startswith("{{ config(")
    for name in ("check_bespoke_model_assembly_only", "check_bespoke_model_final_casts"):
        passes(name, model=model("fct__x", MART), **ASSEMBLY)
    for name in ("check_bespoke_model_no_unused_ctes", "check_bespoke_model_no_subqueries_in_from"):
        passes(name, model=model("fct__x", MART))
    multi_line = MART.replace("{{ config(materialized='table') }}",
                              "{{\n    config(\n        materialized='table'\n        , tags=['x']\n    )\n}}")
    passes("check_bespoke_model_final_casts", model=model("fct__x", multi_line), **ASSEMBLY)
