"""Bespoke dbt-bouncer checks: SQL style (leading commas, explicit joins).

Generic: no project names are hard-coded; behaviour comes from the parameters set in dbt-bouncer.yml.
The SQL is scanned after removing comments, string literals and Jinja, tracking bracket depth, so commas
inside function calls, IN lists and window clauses are never mistaken for select-list or join commas.
"""
from __future__ import annotations

import re

from dbt_bouncer.check_framework.decorator import check, fail

_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
_JINJA_BLOCK = re.compile(r"\{%.*?%\}", re.S)
_JINJA_EXPR = re.compile(r"\{\{.*?\}\}", re.S)
_SQL_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)
_STRING = re.compile(r"'(?:[^']|'')*'")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# clauses that end a FROM list (a comma after one of these is not a comma join)
_FROM_LIST_END = {"join", "where", "group", "qualify", "having", "order", "limit", "union", "window", "except", "intersect", "on", "using"}


def _clean(code: str) -> str:
    """Comments, strings and Jinja replaced by neutral text; line breaks normalised (CRLF-safe)."""
    code = (code or "").replace("\r\n", "\n")
    code = _JINJA_COMMENT.sub("", code)
    code = _JINJA_BLOCK.sub("", code)
    code = _JINJA_EXPR.sub("jinja_expr", code)
    code = _SQL_COMMENT.sub("", code)
    return _STRING.sub("''", code)


def scan_commas(code: str) -> tuple[list[str], list[str]]:
    """Return (list commas not at the start of their line, FROM-list comma joins) for one SQL text.

    List commas are those separating select targets or CTEs. With leading commas every such comma starts
    its line, so one found after other text on the line is either a trailing comma or a second item on the
    same line (`select a, b`).
    """
    misplaced, comma_joins = [], []
    depth = 0
    in_select: dict[int, bool] = {}
    in_from: dict[int, bool] = {}
    in_with: dict[int, bool] = {}
    for line in _clean(code).split("\n"):
        i = 0
        flagged = False
        while i < len(line):
            ch = line[i]
            if ch == "(":
                depth += 1
                in_select[depth] = in_from[depth] = in_with[depth] = False
            elif ch == ")":
                for d in (in_select, in_from, in_with):
                    d.pop(depth, None)
                depth = max(depth - 1, 0)
            elif ch == ",":
                if in_from.get(depth):
                    comma_joins.append(line.strip()[:80])
                elif (in_select.get(depth) or in_with.get(depth)) and line[:i].strip() and not flagged:
                    misplaced.append(line.strip()[:80])
                    flagged = True
            else:
                m = _WORD.match(line, i)
                if m and (i == 0 or not (line[i - 1].isalnum() or line[i - 1] == "_")):
                    word = m.group(0).lower()
                    if word == "with":
                        in_with[depth] = True
                    elif word == "select":
                        in_select[depth], in_from[depth], in_with[depth] = True, False, False
                    elif word == "from" and in_select.get(depth):
                        in_select[depth], in_from[depth] = False, True
                    elif word in _FROM_LIST_END:
                        in_from[depth] = False
                    i = m.end()
                    continue
            i += 1
    return misplaced, comma_joins


@check
def check_bespoke_model_leading_commas(model, *, max_examples: int = 5):
    """Select lists and CTE lists use leading commas, one item per line: every list comma starts its line."""
    misplaced, _ = scan_commas(model.raw_code)
    if misplaced:
        fail(f"`{model.name}` has {len(misplaced)} list line(s) with a comma that does not start the line "
             f"(trailing comma, `),` between CTEs, or several items on one line): {misplaced[:max_examples]}")


@check
def check_bespoke_macro_leading_commas(macro, *, max_examples: int = 5):
    """SQL emitted by macros (and generic tests) uses leading commas, one item per line."""
    misplaced, _ = scan_commas(macro.macro_sql)
    if misplaced:
        fail(f"Macro `{macro.name}` has {len(misplaced)} list line(s) with a comma that does not start the line: "
             f"{misplaced[:max_examples]}")


@check
def check_bespoke_model_explicit_joins(model):
    """Joins are written with a JOIN keyword; no comma joins (`from a, b`) in the FROM list."""
    _, comma_joins = scan_commas(model.raw_code)
    if comma_joins:
        fail(f"`{model.name}` joins with a comma; write an explicit join (e.g. `cross join`): {comma_joins}")


@check
def check_bespoke_macro_explicit_joins(macro):
    """Macro SQL writes joins with a JOIN keyword; no comma joins (`from a, b`) in the FROM list."""
    _, comma_joins = scan_commas(macro.macro_sql)
    if comma_joins:
        fail(f"Macro `{macro.name}` joins with a comma; write an explicit join (e.g. `cross join`): {comma_joins}")
