"""Bespoke dbt-bouncer checks: model structure, layout and documentation.

Generic: no project names are hard-coded; behaviour comes from the parameters set in dbt-bouncer.yml,
so every rule (built-in or bespoke) is defined and scoped in that one file.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from dbt_bouncer.check_framework.decorator import check, fail

_SQL_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)
_JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
_REF = re.compile(r"\{\{\s*ref\(\s*['\"](\w+)['\"]\s*\)\s*\}\}")
_CTE_DEF = re.compile(r"(?:\bwith\b(?:\s+recursive\b)?|,)\s*([A-Za-z_]\w*)\s+as\s*\(", re.I)
_SINGLE_MACRO_BODY = re.compile(r"\s*\{\{\s*\w+\(.*?\)\s*\}\}\s*", re.S)
_DOC_ONLY = re.compile(r"""^\{\{\s*doc\(\s*["'](\w+)["']\s*\)\s*\}\}$""")


def _strip_comments(code: str) -> str:
    return _SQL_COMMENT.sub("", _JINJA_COMMENT.sub("", (code or "").replace("\r\n", "\n")))


def _path_parts(path: str) -> tuple[str, ...]:
    return Path(str(path).replace("\\", "/")).parts


@check
def check_bespoke_model_required_columns(model, *, required_columns: list[str]):
    """The model's properties file declares every required column (e.g. audit fields)."""
    missing = [c for c in required_columns if c not in (model.columns or {})]
    if missing:
        fail(f"`{model.name}` does not declare column(s) {missing} in its properties file.")


@check
def check_bespoke_model_config_value(model, *, config_path: str, expected: Any):
    """A model config value (dot path, e.g. `contract.enforced`) equals the expected value; unset counts as None/False."""
    value: Any = model.config or {}
    for key in config_path.split("."):
        value = value.get(key) if isinstance(value, dict) else getattr(value, key, None)
    if (value or None) != (expected or None):
        fail(f"`{model.name}` has `{config_path}` = {value!r}, expected {expected!r}.")


@check
def check_bespoke_model_properties_file_name(model, *, file_name_template: str):
    """The model is documented in a properties file named by the template ({layer}, {folder}, {model})."""
    parts = _path_parts(model.original_file_path)
    if len(parts) < 4 or parts[0] != "models":
        fail(f"`{model.name}` is not in models/<layer>/<folder>/.")
    expected = file_name_template.format(layer=parts[1], folder=parts[2], model=model.name)
    actual = Path(str(model.patch_path or "").split("://")[-1]).name
    if actual != expected:
        fail(f"`{model.name}` is documented in `{actual or '<none>'}`, expected `{expected}`.")


@check
def check_bespoke_model_cte_layout(
    model,
    *,
    cte_prefix: str = "cte_",
    ref_cte_template: str = "cte_{ref}",
    final_cte: str = "cte_final",
    allow_single_macro_body: bool = True,
):
    """CTE layout: CTEs named with the prefix, one import CTE per ref(), the last CTE is the final CTE,
    the model ends `select * from <final>`, and that is the only `select *`."""
    code = _strip_comments(model.raw_code)
    if allow_single_macro_body and _SINGLE_MACRO_BODY.fullmatch(code):
        return  # the body is one macro call; the layout is checked in the macro
    problems = []
    ctes = _CTE_DEF.findall(code)
    bad = [c for c in ctes if not c.startswith(cte_prefix)]
    if bad:
        problems.append(f"CTEs not prefixed `{cte_prefix}`: {bad}")
    for ref in sorted(set(_REF.findall(code))):
        if ref_cte_template.format(ref=ref) not in ctes:
            problems.append(f"no CTE `{ref_cte_template.format(ref=ref)}` for ref('{ref}')")
    if not ctes or ctes[-1] != final_cte:
        problems.append(f"last CTE is `{ctes[-1] if ctes else None}`, expected `{final_cte}`")
    if not re.search(rf"\bselect\s+\*\s+from\s+{final_cte}\s*$", code.strip(), re.I):
        problems.append(f"does not end with `select * from {final_cte}`")
    if len(re.findall(r"\bselect\s+(?:distinct\s+)?\*", code, re.I)) > 1:
        problems.append("uses `select *` outside the final select; list the columns")
    if problems:
        fail(f"`{model.name}`: " + "; ".join(problems))


@check
def check_bespoke_model_max_joins(model, *, max_joins: int):
    """The model SQL contains at most `max_joins` JOIN keywords (comments ignored)."""
    n = len(re.findall(r"\bjoin\b", _strip_comments(model.raw_code), re.I))
    if n > max_joins:
        fail(f"`{model.name}` has {n} joins (max {max_joins}); split it into focused intermediate models.")


@check
def check_bespoke_model_max_leaf_fanout(model, ctx, *, max_leaf_children: int):
    """At most `max_leaf_children` direct child models that have no children of their own
    (dbt_project_evaluator's fct_model_fanout definition)."""
    child_map = ctx.manifest_obj.manifest.child_map or {}
    children = [c for c in child_map.get(model.unique_id, []) if c.startswith("model.")]
    leaves = [c.split(".")[-1] for c in children
              if not any(g.startswith("model.") for g in child_map.get(c, []))]
    if len(leaves) > max_leaf_children:
        fail(f"`{model.name}` feeds {len(leaves)} leaf models (max {max_leaf_children}): {sorted(leaves)}")


@check
def check_bespoke_model_column_doc_blocks(model, ctx, *, doc_name_pattern: str = "^col__", project_dir: str = "."):
    """Every column description in the properties file is exactly one doc() call to an existing doc block
    whose name matches the pattern. Reads the yml from disk because the manifest holds rendered text."""
    import yaml

    rel = str(model.patch_path or "").split("://")[-1]
    path = Path(project_dir) / rel
    if not rel or not path.exists():
        fail(f"`{model.name}`: properties file `{rel}` not found under `{project_dir}`.")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entry = next((m for m in data.get("models", []) if m.get("name") == model.name), None)
    if entry is None:
        fail(f"`{model.name}` not found in `{rel}`.")
    docs = ctx.manifest_obj.manifest.docs or {}
    problems = []
    for col in entry.get("columns", []) or []:
        desc = str(col.get("description") or "").strip()
        m = _DOC_ONLY.match(desc)
        if not m:
            problems.append(f"{col.get('name')} ({'missing' if not desc else 'literal text'})")
        elif not re.match(doc_name_pattern, m.group(1)) or f"doc.{model.package_name}.{m.group(1)}" not in docs:
            problems.append(f"{col.get('name')} (doc `{m.group(1)}` unknown or not matching {doc_name_pattern})")
    if problems:
        fail(f"`{model.name}` columns without a valid doc() block ({len(problems)}): {problems}")


@check
def check_bespoke_column_descriptions_consistent(ctx, *, own_meaning_blocks: dict[str, str] | None = None):
    """A column name has the same description in every model, except columns that carry a different, declared
    meaning in some models (e.g. a composite of two sources that keeps the name of one of them). `own_meaning_blocks`
    maps such a column name to the doc block holding the other meaning: models whose description is exactly
    that block are a second group, which is consistent by construction; any further variant still fails."""
    docs = ctx.manifest_obj.manifest.docs or {}
    own: dict[str, str] = {}
    for column, block in (own_meaning_blocks or {}).items():
        found = next((d for key, d in docs.items() if key.rsplit(".", 1)[-1] == block), None)
        if found is None:
            fail(f"doc block `{block}` for column `{column}` does not exist.")
        own[column] = (found.block_contents or "").strip()
    variants: dict[str, set[str]] = {}
    for model in ctx.models:
        for name, col in (model.columns or {}).items():
            desc = (getattr(col, "description", "") or "").strip()
            if desc and desc != own.get(name):
                variants.setdefault(name, set()).add(desc)
    conflicts = sorted(name for name, found in variants.items() if len(found) > 1)
    if conflicts:
        fail(f"Columns have conflicting descriptions across models: {conflicts}.")
