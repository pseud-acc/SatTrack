"""Bespoke dbt-bouncer checks: sources and macros.

Generic: file-path templates and thresholds come from the parameters set in dbt-bouncer.yml.
"""
from __future__ import annotations

from dbt_bouncer.check_framework.decorator import check, fail


@check
def check_bespoke_source_file_path(source, *, path_template: str):
    """The source is defined at the path given by the template ({source_name})."""
    expected = path_template.format(source_name=source.source_name)
    actual = str(source.original_file_path).replace("\\", "/")
    if actual != expected:
        fail(f"`{source.source_name}.{source.name}` is defined in `{actual}`, expected `{expected}`.")


@check
def check_bespoke_source_loaded_at_field(source):
    """Freshness is measurable: the source table sets loaded_at_field (or loaded_at_query)."""
    if not (source.loaded_at_field or (source.config or {}).get("loaded_at_query")):
        fail(f"`{source.source_name}.{source.name}` has no loaded_at_field.")


@check
def check_bespoke_macro_arguments_documented(macro, *, require_type: bool = True, min_description_length: int = 4):
    """Every argument in the macro signature is documented with a description (and a type), and no
    documented argument is missing from the signature. Built-in MA001 skips macros with no `arguments:`."""
    from dbt_bouncer.checks.manifest.check_macros import _parse_macro_argument_names

    try:
        signature = _parse_macro_argument_names(macro.macro_sql)
    except Exception as exc:  # noqa: BLE001
        fail(f"`{macro.name}`: could not parse the signature ({exc}).")
    documented = {a.name: a for a in (macro.arguments or [])}
    problems = []
    for arg in signature:
        doc = documented.get(arg)
        if doc is None:
            problems.append(f"{arg} (undocumented)")
            continue
        if require_type and not str(doc.type or "").strip():
            problems.append(f"{arg} (no type)")
        if len(str(doc.description or "").strip()) < min_description_length:
            problems.append(f"{arg} (no description)")
    extra = sorted(set(documented) - set(signature))
    if extra:
        problems.append(f"documented but not in the signature: {extra}")
    if problems:
        fail(f"Macro `{macro.name}`: {problems}")


@check
def check_bespoke_one_macro_per_file(macro, ctx):
    """A macro file defines exactly one macro."""
    same_file = [m.name for m in ctx.macros if m.original_file_path == macro.original_file_path]
    if len(same_file) > 1:
        fail(f"`{macro.original_file_path}` defines {len(same_file)} macros: {sorted(same_file)}.")
