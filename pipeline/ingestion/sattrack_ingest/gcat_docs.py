"""Parse GCAT's code tables from its documentation pages into label records (plan section 15.1).

No human wording: gcat_meaning is GCAT's text verbatim; short_label is derived by a fixed rule:
  1. cut at the first comma or sentence end that is outside brackets;
  2. drop a bracketed part of 18+ characters ("Civil (government but not military)" -> "Civil"),
     keep short qualifiers ("Imaging (optical)", "Business (commercial)").
Raises GcatDocsError when the page layout changes or two short labels collide, so the enrichment unit
fails closed and keeps its last good build. Codes GCAT adds later get labels on the next run.
"""
from __future__ import annotations

import html
import re

CODE_LABELS_URL = "https://planet4589.org/space/gcat/web/cat/pcols.html"
# label domain -> sentence that precedes its table on the page
CODE_LABEL_TABLES = {
    "mission_category": "The defined categories are",
    "ownership_class": "The four supported single-letter values are",
}


class GcatDocsError(RuntimeError):
    pass


def _table_after(page: str, marker: str) -> list[tuple[str, str]]:
    i = page.find(marker)
    if i < 0:
        raise GcatDocsError(f"marker not found on {CODE_LABELS_URL}: {marker!r} (page layout changed?)")
    j = page.upper().find("<TABLE", i)
    k = page.upper().find("</TABLE", j)
    rows = re.findall(r"<TR>\s*<TD>\s*([^<]+?)\s*<TD>\s*(.+?)\s*</TR>", page[j:k], flags=re.I | re.S)
    if not rows:
        raise GcatDocsError(f"no rows parsed after {marker!r}")
    return [(html.unescape(c).strip(), re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m))).strip())
            for c, m in rows]


def short_label(meaning: str) -> str:
    depth, cut = 0, len(meaning)
    for idx, ch in enumerate(meaning):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        elif depth == 0 and (ch == "," or (ch == "." and (idx + 1 == len(meaning) or meaning[idx + 1] == " "))):
            cut = idx
            break
    text = meaning[:cut].strip()
    text = re.sub(r"\s*\(([^()]{18,})\)", "", text).strip()   # drop long bracketed parts (18+ chars)
    return text.rstrip(".").strip()


def parse_code_labels(page: str) -> list[dict]:
    records = []
    for domain, marker in CODE_LABEL_TABLES.items():
        rows = _table_after(page, marker)
        labels = [short_label(m) for _, m in rows]
        dupes = sorted({lbl for lbl in labels if labels.count(lbl) > 1})
        if dupes:
            raise GcatDocsError(f"{domain}: short labels collide: {dupes}; adjust the rule, not the labels")
        records += [{"domain": domain, "gcat_code": code, "gcat_meaning": meaning, "short_label": label}
                    for (code, meaning), label in zip(rows, labels)]
    return records
