"""Every bespoke check (defined in bespoke/ or configured in dbt-bouncer.yml) is exercised by this suite."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from conftest import BESPOKE_DIR, CONFIG_FILE

TESTS_DIR = Path(__file__).resolve().parent


def _defined() -> set[str]:
    names = set()
    for f in BESPOKE_DIR.glob("*/*.py"):
        names |= set(re.findall(r"^@check\s*\ndef (check_\w+)\(", f.read_text(encoding="utf-8"), re.M))
    return names


def _configured() -> set[str]:
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    return {c["name"] for c in config.get("manifest_checks", []) if c["name"].startswith("check_bespoke_")}


def _tested() -> set[str]:
    text = "".join(f.read_text(encoding="utf-8") for f in TESTS_DIR.glob("test_bespoke_*.py"))
    return set(re.findall(r"\"(check_bespoke_\w+)\"", text))


def test_every_configured_bespoke_check_is_defined():
    assert _configured() <= _defined(), sorted(_configured() - _defined())


def test_every_bespoke_check_has_tests():
    assert _defined(), "no bespoke checks found"
    assert _defined() <= _tested(), sorted(_defined() - _tested())
