"""Bespoke dbt-bouncer checks: SQL semantics, parsed with sqlglot (a dbt-bouncer dependency).

The model's raw SQL is parsed after replacing its Jinja with placeholders, so these checks run on the
`dbt parse` manifest (no compile step, no warehouse):
  {{ ref('x') }}          -> x                (a table named after the model)
  {{ source('s', 't') }}  -> s__t
  {{ helper__m(...) }}    -> helper__m()      (a function call named after the macro)
Generic: thresholds, CTE names and allow-lists come from the parameters set in dbt-bouncer.yml.
"""
from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

from dbt_bouncer.check_framework.decorator import check, fail

_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
_JINJA_BLOCK = re.compile(r"\{%.*?%\}", re.S)
_CONFIG = re.compile(r"\{\{\s*config\(.*?\)\s*\}\}", re.S)  # renders to nothing in dbt
_REF = re.compile(r"\{\{\s*ref\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")
_SOURCE = re.compile(r"\{\{\s*source\(\s*['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\s*\)\s*\}\}")
_MACRO = re.compile(r"\{\{\s*(?:\w+\.)?(\w+)\s*\(.*?\)\s*\}\}", re.S)
_ANY_JINJA = re.compile(r"\{\{.*?\}\}", re.S)
_SINGLE_MACRO_BODY = re.compile(r"\s*\{\{\s*\w+\(.*?\)\s*\}\}\s*", re.S)


def _parse(model, dialect: str) -> exp.Expression | None:
    """sqlglot tree of the model with Jinja replaced; None if the body is a single macro call."""
    code = _CONFIG.sub("", _JINJA_BLOCK.sub("", _JINJA_COMMENT.sub("", model.raw_code or "")))
    if _SINGLE_MACRO_BODY.fullmatch(code):
        return None
    code = _REF.sub(lambda m: m.group(1), code)
    code = _SOURCE.sub(lambda m: f"{m.group(1)}__{m.group(2)}", code)
    code = _MACRO.sub(lambda m: f"{m.group(1)}()", code)
    code = _ANY_JINJA.sub("null", code)
    try:
        return sqlglot.parse_one(code, read=dialect)
    except sqlglot.errors.ParseError as exc:
        fail(f"`{model.name}`: sqlglot could not parse the SQL ({str(exc).splitlines()[0][:120]}).")


def _ctes(tree: exp.Expression) -> dict[str, exp.Expression]:
    return {c.alias: c.this for c in tree.find_all(exp.CTE)}


def _select_of(query: exp.Expression) -> exp.Select | None:
    return query if isinstance(query, exp.Select) else query.find(exp.Select)


def _is_constant(node: exp.Expression) -> bool:
    """A literal, NULL, boolean, array of constants, or a cast of one (e.g. cast([] as varchar[]))."""
    if isinstance(node, (exp.Literal, exp.Null, exp.Boolean)):
        return True
    if isinstance(node, exp.Cast):
        return _is_constant(node.this)
    if isinstance(node, exp.Array):
        return all(_is_constant(e) for e in node.expressions)
    if isinstance(node, exp.Paren):
        return _is_constant(node.this)
    return False


def _sources_read(node: exp.Expression, alias_to_relation: dict[str, str], only_relation: str | None) -> set[str]:
    """Relations (CTE or table names) whose columns the expression reads."""
    out = set()
    for col in node.find_all(exp.Column):
        if col.table:
            out.add(alias_to_relation.get(col.table, col.table))
        elif only_relation:
            out.add(only_relation)
        else:
            out.add("<unqualified>")
    return out


@check
def check_bespoke_model_assembly_only(
    model,
    *,
    dialect: str = "duckdb",
    import_cte_template: str = "cte_{ref}",
    final_cte: str = "cte_final",
    default_functions: list[str] = ["coalesce"],  # noqa: B006
    min_relations_for_logic: int = 2,
    allowed_macros: list[str] = [],  # noqa: B006
):
    """Marts only assemble: outside the import CTEs and the final CTE, every select target is a column,
    a default for an unmatched join (`coalesce(column, constant)`), or logic that reads at least
    `min_relations_for_logic` relations. Logic that reads one upstream model belongs in that model."""
    tree = _parse(model, dialect)
    if tree is None:
        return
    import_ctes = {import_cte_template.format(ref=r) for r in _REF.findall(model.raw_code or "")}
    problems = []
    for name, query in _ctes(tree).items():
        if name in import_ctes or name == final_cte:
            continue
        sel = _select_of(query)
        if sel is None:
            continue
        alias_to_relation = {t.alias_or_name: t.name for t in sel.find_all(exp.Table)}
        relations = set(alias_to_relation.values())
        only = next(iter(relations)) if len(relations) == 1 else None
        for proj in sel.expressions:
            node = proj.this if isinstance(proj, exp.Alias) else proj
            if isinstance(node, (exp.Column, exp.Star)):
                continue
            if isinstance(node, exp.Anonymous) and node.name in allowed_macros:
                continue
            fn = node.sql_name().lower() if isinstance(node, exp.Func) else ""
            args = [node.this, *node.expressions] if isinstance(node, exp.Func) else []
            if fn in default_functions and args and isinstance(args[0], exp.Column) and all(_is_constant(a) for a in args[1:]):
                continue
            read = _sources_read(node, alias_to_relation, only)
            if "<unqualified>" in read:
                problems.append(f"{name}.{proj.alias_or_name}: qualify the columns so the source can be traced")
            elif len(read) < min_relations_for_logic:
                problems.append(f"{name}.{proj.alias_or_name}: logic reads only {sorted(read)}; move it into that model")
    if problems:
        fail(f"`{model.name}` transforms data from a single upstream model: {problems}")


@check
def check_bespoke_model_final_casts(
    model,
    *,
    dialect: str = "duckdb",
    final_cte: str = "cte_final",
    allowed_macros: list[str] = [],  # noqa: B006
):
    """Every target of the final CTE is `cast(<column> as <type>) as <same name>`, so the intended table
    schema is visible in the SQL (allowed macros such as the audit fields excepted)."""
    tree = _parse(model, dialect)
    if tree is None:
        return
    query = _ctes(tree).get(final_cte)
    if query is None:
        fail(f"`{model.name}` has no `{final_cte}` CTE.")
    problems = []
    for proj in _select_of(query).expressions:
        node = proj.this if isinstance(proj, exp.Alias) else proj
        if isinstance(node, exp.Anonymous) and node.name in allowed_macros:
            continue
        if not isinstance(node, exp.Cast) or not isinstance(node.this, exp.Column):
            problems.append(f"{proj.alias_or_name} (not a cast of a column)")
        elif node.this.name != proj.alias_or_name:
            problems.append(f"{proj.alias_or_name} (casts `{node.this.name}` under a new name; rename upstream)")
    if problems:
        fail(f"`{model.name}` final columns without an explicit cast: {problems}")


@check
def check_bespoke_model_select_targets_allowed(
    model,
    *,
    dialect: str = "duckdb",
    allowed_functions: list[str] = [],  # noqa: B006
    allowed_macros: list[str] = [],  # noqa: B006
):
    """Every select target is a column, a constant, a cast, or built only from the allowed functions
    and macros (e.g. staging may only rename, cast and clean)."""
    tree = _parse(model, dialect)
    if tree is None:
        return
    allowed = {f.lower() for f in allowed_functions}
    problems = []
    for sel in tree.find_all(exp.Select):
        for proj in sel.expressions:
            node = proj.this if isinstance(proj, exp.Alias) else proj
            used = set()
            for n in node.walk():
                if isinstance(n, exp.Anonymous):
                    if n.name not in allowed_macros and n.name.lower() not in allowed:
                        used.add(n.name)
                elif isinstance(n, exp.Func) and not isinstance(n, exp.Cast):
                    if n.sql_name().lower() not in allowed:
                        used.add(n.sql_name().lower())
                elif isinstance(n, (exp.Binary, exp.Case, exp.Subquery, exp.Window)) and not isinstance(n, exp.Dot):
                    used.add(type(n).__name__.lower())
            if used:
                problems.append(f"{proj.alias_or_name} uses {sorted(used)}")
    if problems:
        fail(f"`{model.name}` select targets beyond rename/cast/allowed functions: {problems}")


@check
def check_bespoke_model_no_unused_ctes(model, *, dialect: str = "duckdb"):
    """Every CTE is read by a later CTE or the final select."""
    tree = _parse(model, dialect)
    if tree is None:
        return
    read = {t.name for t in tree.find_all(exp.Table)}
    # a CTE passed to a macro by name (e.g. helper__explode_org_codes('cte_x', ...)) is read by the macro
    macro_args = " ".join(_ANY_JINJA.findall(model.raw_code or ""))
    unused = [name for name in _ctes(tree) if name not in read and not re.search(rf"\b{name}\b", macro_args)]
    if unused:
        fail(f"`{model.name}` defines CTEs that nothing reads: {unused}")


@check
def check_bespoke_model_no_subqueries_in_from(model, *, dialect: str = "duckdb"):
    """FROM and JOIN read CTEs or relations, never inline subqueries; give the subquery a named CTE."""
    tree = _parse(model, dialect)
    if tree is None:
        return
    found = []
    for sub in tree.find_all(exp.Subquery):
        if isinstance(sub.parent, (exp.From, exp.Join)):
            found.append(sub.alias_or_name or sub.sql(dialect=dialect)[:60])
    if found:
        fail(f"`{model.name}` has subqueries in FROM/JOIN: {found}")
