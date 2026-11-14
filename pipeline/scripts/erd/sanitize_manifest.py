"""Make a dbt 2.0 manifest.json readable by dbterd's manifest-v12 parser.

The only known incompatibility (dbterd 1.32.0 with dbt-oss 2.0.8): `unit_tests.*.checksum` is an object
{"name": ..., "checksum": ...} where the v12 schema wants a string. The checksum is flattened to its value; nothing
else in the manifest is touched.

  python scripts/erd/sanitize_manifest.py <manifest.json in> <manifest.json out>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def flatten_unit_test_checksums(manifest: dict) -> int:
    """Replace each object-valued unit test checksum with its string value; return how many were changed."""
    fixed = 0
    for unit_test in manifest.get("unit_tests", {}).values():
        checksum = unit_test.get("checksum")
        if isinstance(checksum, dict):
            unit_test["checksum"] = checksum.get("checksum", "")
            fixed += 1
    return fixed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", type=Path, help="manifest.json written by dbt")
    ap.add_argument("dst", type=Path, help="where to write the sanitized copy")
    args = ap.parse_args()
    manifest = json.loads(args.src.read_text(encoding="utf-8"))
    fixed = flatten_unit_test_checksums(manifest)
    args.dst.write_text(json.dumps(manifest), encoding="utf-8")
    print(f"unit test checksums flattened: {fixed}")


if __name__ == "__main__":
    main()
