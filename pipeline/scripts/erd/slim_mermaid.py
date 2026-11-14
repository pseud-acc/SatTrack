"""Reduce dbterd's full-column Mermaid ER diagram to the key columns.

Only the columns that take part in a relationship are kept, tagged PK (parent side) or FK (child side); the
relationship lines are copied unchanged. A diagram with every column of every mart is unreadable; the full column
list is in the docs site.

  python scripts/erd/slim_mermaid.py <full.mmd in> <slim.mmd out>
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

RELATIONSHIP = re.compile(r'^\s+"(\w+)" (\S+) "(\w+)": (.+)$')   # "child" <cardinality> "parent": parent_col--child_col
ENTITY_OPEN = re.compile(r'^  "(\w+)" \{$')


def relationship_columns(lines: list[str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return (child columns, parent columns) per entity, read from the relationship lines."""
    child_cols: dict[str, set[str]] = {}
    parent_cols: dict[str, set[str]] = {}
    for line in lines:
        m = RELATIONSHIP.match(line)
        if not m:
            continue
        child, _, parent, cols = m.groups()
        parent_col, _, child_col = cols.partition("--")   # "parent_col--child_col", or one name when both are the same
        child_col = child_col or parent_col
        child_cols.setdefault(child, set()).add(child_col)
        parent_cols.setdefault(parent, set()).add(parent_col)
    return child_cols, parent_cols


def slim(lines: list[str]) -> list[str]:
    child_cols, parent_cols = relationship_columns(lines)
    out: list[str] = []
    entity = None
    for line in lines:
        m = ENTITY_OPEN.match(line)
        if m:
            entity = m.group(1)
            out.append(line)
            continue
        if line.strip() == "}":
            entity = None
            out.append(line)
            continue
        if entity is None:
            out.append(line)
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        col_type, col = parts
        if col in parent_cols.get(entity, ()):
            out.append(f"    {col_type} {col} PK")
        elif col in child_cols.get(entity, ()):
            out.append(f"    {col_type} {col} FK")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", type=Path, help="Mermaid file written by dbterd with all columns")
    ap.add_argument("dst", type=Path, help="where to write the key-columns-only diagram")
    args = ap.parse_args()
    lines = args.src.read_text(encoding="utf-8").splitlines()
    args.dst.write_text("\n".join(slim(lines)) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
