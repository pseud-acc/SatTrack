"""Render a Mermaid file to SVG with headless Microsoft Edge (Windows, local use only).

The docs workflow renders with the pinned @mermaid-js/mermaid-cli (scripts/erd/build_erd.sh). This script is the
local fallback for a machine without Node: Edge loads a pinned mermaid.js from jsDelivr and the SVG is read back
from the rendered page. The theme and size options match the ones build_erd.sh passes to mermaid-cli.

  python scripts/erd/mermaid_to_svg_edge.py <in.mmd> <out.svg>
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
PAGE = """<!doctype html><meta charset="utf-8"><body>
<pre class="mermaid" id="m">{diagram}</pre>
<script src="{script}"></script>
<script>mermaid.initialize({{startOnLoad: true, theme: 'neutral', er: {{useMaxWidth: false}}}});</script>
"""


def render(diagram: str) -> str:
    """Return the SVG that Edge draws for a Mermaid diagram."""
    page = PAGE.format(diagram=html.escape(diagram), script=MERMAID_JS)
    with tempfile.TemporaryDirectory() as tmp:
        page_path = Path(tmp) / "render.html"
        page_path.write_text(page, encoding="utf-8")
        dom = subprocess.run(
            [EDGE, "--headless=new", "--disable-gpu", "--virtual-time-budget=15000", "--dump-dom", page_path.as_uri()],
            capture_output=True, text=True, encoding="utf-8", timeout=120, check=True,
        ).stdout
    m = re.search(r"<svg.*?</svg>", dom, re.S)
    if not m:
        sys.exit("no svg in the rendered page")
    svg = m.group(0)
    if "xmlns=" not in svg[:200]:
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    return svg.replace("<svg ", '<svg style="background-color:#ffffff" ', 1)   # readable on a dark docs theme


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", type=Path, help="Mermaid file")
    ap.add_argument("dst", type=Path, help="SVG file to write")
    args = ap.parse_args()
    svg = render(args.src.read_text(encoding="utf-8"))
    args.dst.write_text(svg, encoding="utf-8")
    print(f"wrote {args.dst} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
