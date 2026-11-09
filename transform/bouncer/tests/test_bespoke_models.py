"""Tests for bespoke/manifest/bespoke_models.py: model structure, layout and documentation."""
from __future__ import annotations

from conftest import fails, model, passes, sql

AUDIT = ["inserted_date_time", "inserted_by"]

GOOD_LAYOUT = sql("""
    with cte_stg__a__x as (
        select
            x_id
            , x_name
        from {{ ref('stg__a__x') }}
    )

    , cte_named as (
        select
            x_id
            , upper(x_name) as x_name
        from cte_stg__a__x
    )

    , cte_final as (
        select
            x_id
            , x_name
            , {{ helper__audit_fields() }}
        from cte_named
    )

    select * from cte_final
""")


# ---------------------------------------------------------------- check_bespoke_model_required_columns
def test_required_columns_pass():
    passes("check_bespoke_model_required_columns",
           model=model(columns={"x_id": {}, "inserted_date_time": {}, "inserted_by": {}}),
           required_columns=AUDIT)


def test_required_columns_fail_names_missing():
    fails("check_bespoke_model_required_columns", match="inserted_by",
          model=model(columns={"x_id": {}, "inserted_date_time": {}}), required_columns=AUDIT)


def test_required_columns_fail_when_no_columns():
    fails("check_bespoke_model_required_columns", model=model(columns={}), required_columns=AUDIT)


# ---------------------------------------------------------------- check_bespoke_model_config_value
def test_config_value_pass():
    passes("check_bespoke_model_config_value", model=model(config={"contract": {"enforced": True}}),
           config_path="contract.enforced", expected=True)


def test_config_value_unset_counts_as_false():
    passes("check_bespoke_model_config_value", model=model(config={}),
           config_path="contract.enforced", expected=False)
    passes("check_bespoke_model_config_value", model=model(config={"contract": {}}),
           config_path="contract.enforced", expected=False)


def test_config_value_fail():
    fails("check_bespoke_model_config_value", match="contract.enforced",
          model=model(config={"contract": {"enforced": True}}), config_path="contract.enforced", expected=False)


def test_config_value_fail_when_required_but_unset():
    fails("check_bespoke_model_config_value", model=model(config={}),
          config_path="contract.enforced", expected=True)


# ---------------------------------------------------------------- check_bespoke_model_properties_file_name
def test_properties_file_name_pass():
    passes("check_bespoke_model_properties_file_name",
           model=model(original_file_path="models/intermediate/satellite/int__a__b.sql",
                       patch_path="sattrack://models/intermediate/satellite/_int_satellite__schema.yml"),
           file_name_template="_int_{folder}__schema.yml")


def test_properties_file_name_windows_path_pass():
    passes("check_bespoke_model_properties_file_name",
           model=model(original_file_path="models\\marts\\geography\\dim__country.sql",
                       patch_path="sattrack://models/marts/geography/_geography__schema.yml"),
           file_name_template="_{folder}__schema.yml")


def test_properties_file_name_fail_wrong_name():
    fails("check_bespoke_model_properties_file_name", match="expected `_int_satellite__schema.yml`",
          model=model(original_file_path="models/intermediate/satellite/int__a__b.sql",
                      patch_path="sattrack://models/intermediate/satellite/_satellite__schema.yml"),
          file_name_template="_int_{folder}__schema.yml")


def test_properties_file_name_fail_undocumented():
    fails("check_bespoke_model_properties_file_name", match="<none>",
          model=model(original_file_path="models/intermediate/satellite/int__a__b.sql", patch_path=None),
          file_name_template="_int_{folder}__schema.yml")


def test_properties_file_name_fail_outside_layer_folder():
    fails("check_bespoke_model_properties_file_name", match="not in models/<layer>/<folder>/",
          model=model(original_file_path="models/int__a__b.sql", patch_path="sattrack://models/_x.yml"),
          file_name_template="_int_{folder}__schema.yml")


# ---------------------------------------------------------------- check_bespoke_model_cte_layout
def test_cte_layout_pass():
    passes("check_bespoke_model_cte_layout", model=model(raw_code=GOOD_LAYOUT))


def test_cte_layout_pass_crlf_and_comments():
    code = "-- select * from somewhere\n{# select * #}\n" + GOOD_LAYOUT + "\n/* trailing */\n"
    passes("check_bespoke_model_cte_layout", model=model(raw_code=code.replace("\n", "\r\n")))


def test_cte_layout_pass_with_recursive():
    code = GOOD_LAYOUT.replace("with cte_stg__a__x", "with recursive cte_stg__a__x")
    passes("check_bespoke_model_cte_layout", model=model(raw_code=code))


def test_cte_layout_fail_unprefixed_first_cte_after_with_recursive():
    code = GOOD_LAYOUT.replace("with cte_stg__a__x as (", "with recursive walk as (\n    select 1 as x_id\n)\n\n, cte_stg__a__x as (")
    fails("check_bespoke_model_cte_layout", match=r"not prefixed `cte_`: \['walk'\]", model=model(raw_code=code))


def test_cte_layout_pass_single_macro_body():
    passes("check_bespoke_model_cte_layout",
           model=model(raw_code="{{ helper__stage_gcat('gcat', 'satcat', ['a', 'b']) }}\n"))


def test_cte_layout_single_macro_body_not_allowed():
    fails("check_bespoke_model_cte_layout", model=model(raw_code="{{ helper__stage_gcat('gcat') }}"),
          allow_single_macro_body=False)


def test_cte_layout_staging_single_final_cte_pass():
    code = sql("""
        with cte_final as (
            select
                cast(a as integer) as a
            from {{ source('gcat', 'satcat') }}
        )

        select * from cte_final
    """)
    passes("check_bespoke_model_cte_layout", model=model(raw_code=code))


def test_cte_layout_fail_unprefixed_cte():
    fails("check_bespoke_model_cte_layout", match=r"not prefixed `cte_`: \['named'\]",
          model=model(raw_code=GOOD_LAYOUT.replace("cte_named", "named")))


def test_cte_layout_fail_ref_without_import_cte():
    fails("check_bespoke_model_cte_layout", match=r"no CTE `cte_stg__a__x` for ref\('stg__a__x'\)",
          model=model(raw_code=GOOD_LAYOUT.replace("cte_stg__a__x", "cte_import")))


def test_cte_layout_fail_final_not_last():
    code = GOOD_LAYOUT.replace("select * from cte_final",
                               ", cte_extra as (\n    select x_id from cte_final\n)\n\nselect * from cte_final")
    fails("check_bespoke_model_cte_layout", match="last CTE is `cte_extra`", model=model(raw_code=code))


def test_cte_layout_fail_does_not_end_with_final_select():
    code = GOOD_LAYOUT.replace("select * from cte_final", "select x_id, x_name from cte_final")
    fails("check_bespoke_model_cte_layout", match="does not end with", model=model(raw_code=code))


def test_cte_layout_fail_extra_select_star():
    code = GOOD_LAYOUT.replace("select\n        x_id\n        , x_name\n    from {{ ref",
                               "select *\n    from {{ ref")
    fails("check_bespoke_model_cte_layout", match="outside the final select", model=model(raw_code=code))


def test_cte_layout_fail_select_distinct_star():
    code = GOOD_LAYOUT.replace("select\n        x_id\n        , upper", "select distinct *\n        , upper")
    fails("check_bespoke_model_cte_layout", match="outside the final select", model=model(raw_code=code))


def test_cte_layout_custom_names():
    code = GOOD_LAYOUT.replace("cte_", "q_")
    passes("check_bespoke_model_cte_layout", model=model(raw_code=code),
           cte_prefix="q_", ref_cte_template="q_{ref}", final_cte="q_final")


# ---------------------------------------------------------------- check_bespoke_model_max_joins
TWO_JOINS = sql("""
    select a.x
    from a
    left join b on a.id = b.id
    inner join c on a.id = c.id
    -- join d (commented out)
    /* full outer join e */
""")


def test_max_joins_pass_ignores_comments():
    passes("check_bespoke_model_max_joins", model=model(raw_code=TWO_JOINS), max_joins=2)


def test_max_joins_fail():
    fails("check_bespoke_model_max_joins", match="has 2 joins", model=model(raw_code=TWO_JOINS), max_joins=1)


def test_max_joins_ignores_identifiers_containing_join():
    passes("check_bespoke_model_max_joins", model=model(raw_code="select joined_at, join_key from a"), max_joins=0)


# ---------------------------------------------------------------- check_bespoke_model_max_leaf_fanout
def _child_map(leaves: int, non_leaves: int = 0) -> dict:
    parent = "model.sattrack.int__a__b"
    kids = [f"model.sattrack.leaf_{i}" for i in range(leaves)] + [f"model.sattrack.mid_{i}" for i in range(non_leaves)]
    cmap = {parent: kids + ["test.sattrack.mh__int__a__b__pk_unique", "exposure.sattrack.app"]}
    for k in kids:
        cmap[k] = ["test.sattrack.t"]  # tests and exposures do not make a child a non-leaf
    for i in range(non_leaves):
        cmap[f"model.sattrack.mid_{i}"].append(f"model.sattrack.grandchild_{i}")
    return cmap


def test_max_leaf_fanout_pass_non_leaf_children_do_not_count():
    passes("check_bespoke_model_max_leaf_fanout", model=model(),
           ctx_manifest_obj={"child_map": _child_map(leaves=3, non_leaves=5)}, max_leaf_children=3)


def test_max_leaf_fanout_fail():
    fails("check_bespoke_model_max_leaf_fanout", match="feeds 4 leaf models", model=model(),
          ctx_manifest_obj={"child_map": _child_map(leaves=4)}, max_leaf_children=3)


def test_max_leaf_fanout_pass_no_children():
    passes("check_bespoke_model_max_leaf_fanout", model=model(), ctx_manifest_obj={"child_map": {}},
           max_leaf_children=0)


# ---------------------------------------------------------------- check_bespoke_model_column_doc_blocks
def _doc_blocks_setup(tmp_path, columns_yaml: str) -> dict:
    folder = tmp_path / "models" / "marts" / "geography"
    folder.mkdir(parents=True)
    (folder / "_geography__schema.yml").write_text(
        "models:\n  - name: dim__country\n    columns:\n" + columns_yaml, encoding="utf-8")
    return model(name="dim__country", patch_path="sattrack://models/marts/geography/_geography__schema.yml")


DOCS = {"docs": {"doc.sattrack.col__country_key": {}, "doc.sattrack.col__country_name": {}, "doc.sattrack.other": {}}}


def test_column_doc_blocks_pass(tmp_path):
    m = _doc_blocks_setup(tmp_path, (
        "      - name: country_key\n        description: '{{ doc(\"col__country_key\") }}'\n"
        "      - name: country_name\n        description: \"{{ doc('col__country_name') }}\"\n"))
    passes("check_bespoke_model_column_doc_blocks", model=m, ctx_manifest_obj=DOCS, project_dir=str(tmp_path))


def test_column_doc_blocks_fail_literal_missing_unknown_and_pattern(tmp_path):
    m = _doc_blocks_setup(tmp_path, (
        "      - name: a\n        description: Literal text.\n"
        "      - name: b\n"
        "      - name: c\n        description: '{{ doc(\"col__nope\") }}'\n"
        "      - name: d\n        description: '{{ doc(\"other\") }}'\n"
        "      - name: e\n        description: '{{ doc(\"col__country_key\") }} plus text'\n"))
    fails("check_bespoke_model_column_doc_blocks",
          match=r"\(5\).*a \(literal text\).*b \(missing\).*c \(doc `col__nope`.*d \(doc `other`.*e \(literal text\)",
          model=m, ctx_manifest_obj=DOCS, project_dir=str(tmp_path))


def test_column_doc_blocks_fail_properties_file_missing(tmp_path):
    fails("check_bespoke_model_column_doc_blocks", match="not found",
          model=model(name="dim__country", patch_path="sattrack://models/marts/x/_x__schema.yml"),
          ctx_manifest_obj=DOCS, project_dir=str(tmp_path))


def test_column_doc_blocks_fail_model_not_in_file(tmp_path):
    m = _doc_blocks_setup(tmp_path, "      - name: a\n")
    m["name"] = "dim__other"
    fails("check_bespoke_model_column_doc_blocks", match="`dim__other` not found",
          model=m, ctx_manifest_obj=DOCS, project_dir=str(tmp_path))


# ---------------------------------------------------------------- check_bespoke_column_descriptions_consistent
def _col_model(name: str, **descriptions: str) -> dict:
    return model(name=name, columns={c: {"name": c, "description": d} for c, d in descriptions.items()})


CONSISTENT_DOCS = {"docs": {"doc.sattrack.col__object_type__resolved": {"block_contents": "Composite object type."}}}
OWN_MEANING = {"object_type": "col__object_type__resolved"}


def test_column_descriptions_consistent_pass_same_everywhere():
    passes("check_bespoke_column_descriptions_consistent", ctx_manifest_obj=CONSISTENT_DOCS,
           ctx_models=[_col_model("a", object_type="Raw.", x="X."), _col_model("b", object_type="Raw.")])


def test_column_descriptions_consistent_pass_declared_second_meaning():
    passes("check_bespoke_column_descriptions_consistent", ctx_manifest_obj=CONSISTENT_DOCS,
           ctx_models=[_col_model("a", object_type="Raw."), _col_model("b", object_type="Composite object type."),
                       _col_model("c", object_type="Composite object type.")],
           own_meaning_blocks=OWN_MEANING)


def test_column_descriptions_consistent_fail_undeclared_difference():
    fails("check_bespoke_column_descriptions_consistent", match=r"conflicting descriptions.*\['x'\]",
          ctx_manifest_obj=CONSISTENT_DOCS,
          ctx_models=[_col_model("a", x="One."), _col_model("b", x="Two.")], own_meaning_blocks=OWN_MEANING)


def test_column_descriptions_consistent_fail_third_variant_beside_declared_meaning():
    fails("check_bespoke_column_descriptions_consistent", match=r"\['object_type'\]", ctx_manifest_obj=CONSISTENT_DOCS,
          ctx_models=[_col_model("a", object_type="Raw."), _col_model("b", object_type="Composite object type."),
                      _col_model("c", object_type="Something else.")],
          own_meaning_blocks=OWN_MEANING)


def test_column_descriptions_consistent_fail_declared_block_missing():
    fails("check_bespoke_column_descriptions_consistent", match="does not exist",
          ctx_models=[_col_model("a", object_type="Raw.")], own_meaning_blocks=OWN_MEANING)
