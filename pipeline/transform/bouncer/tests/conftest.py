"""Shared helpers for the bespoke dbt-bouncer check tests.

The checks are exercised through dbt-bouncer's own test harness (`dbt_bouncer.testing`), which builds the
resources the same way the runner does: each model, source, macro and test is a `DictProxy` (a dict with
attribute access, missing keys read as None) and the context is a `CheckContext` built from the same lists.
The checks are looked up by name from bouncer/bespoke, exactly as `custom_checks_dir` does at run time.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from dbt_bouncer.testing import check_fails, check_passes

BESPOKE_DIR = Path(__file__).resolve().parents[1] / "bespoke"
CONFIG_FILE = Path(__file__).resolve().parents[1] / "dbt-bouncer.yml"


def sql(text: str) -> str:
    """Dedent a triple-quoted SQL snippet so tests can indent it with the code."""
    return textwrap.dedent(text).strip("\n")


def passes(name: str, **kwargs) -> None:
    check_passes(name, custom_checks_dir=BESPOKE_DIR, **kwargs)


def fails(name: str, match: str | None = None, **kwargs) -> None:
    check_fails(name, custom_checks_dir=BESPOKE_DIR, match=match, **kwargs)


def model(name: str = "int__a__b", raw_code: str = "", **fields) -> dict:
    """A model resource as dbt-bouncer passes it (only the fields the checks read)."""
    return {
        "name": name,
        "unique_id": f"model.sattrack.{name}",
        "package_name": "sattrack",
        "raw_code": raw_code,
        **fields,
    }


def macro(name: str = "helper__m", macro_sql: str = "", **fields) -> dict:
    return {
        "name": name,
        "unique_id": f"macro.sattrack.{name}",
        "package_name": "sattrack",
        "macro_sql": macro_sql,
        "original_file_path": f"macros/helpers/{name}.sql",
        **fields,
    }
