"""
The design tokens (D-044, roadmap 3.12) for code that can't read CSS variables: Plotly figures draw in WebGL and
their hover labels take literal colours. The values are read from assets/03_tokens.css, the single source, when the
app starts, so the two can't drift. Use TOKENS["st-active"] etc.; a missing name fails at import.
"""

import re
from pathlib import Path

TOKENS_CSS = Path(__file__).resolve().parents[2] / "assets" / "03_tokens.css"

# `--st-name: <value>;` inside the first :root block (the token definitions; later blocks map them onto Bootstrap)
_ROOT = re.compile(r":root\s*\{(.*?)\}", re.S)
_DECL = re.compile(r"--(st-[a-z0-9-]+)\s*:\s*([^;]+);")


def read_tokens(path: Path = TOKENS_CSS) -> dict:
    """{token name without the leading dashes: value as written}, e.g. {"st-active": "#f07a6e", ...}."""
    block = _ROOT.search(path.read_text(encoding="utf-8")).group(1)
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    return {name: value.strip() for name, value in _DECL.findall(block)}


TOKENS = read_tokens()
