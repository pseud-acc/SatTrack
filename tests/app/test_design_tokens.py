"""The design foundation (D-044, roadmap 3.12): the committed Bootstrap 5.3.8 and Source Sans 3 files are the pinned
upstream ones, no page loads a stylesheet, font or icon set from a third party, the old Bootstrap 4 files are gone,
assets/ loads in the intended order, and the token colours meet WCAG contrast. Expected values come from the upstream
packages (npm bootstrap 5.3.8, @fontsource-variable/source-sans-3 5.3.1, sha512-verified on download) and the WCAG
2.x relative-luminance formula, not from the app."""
import hashlib
import re

import pytest

from _support import REPO_ROOT

ASSETS = REPO_ROOT / "assets"
TOKENS = ASSETS / "03_tokens.css"

# SHA-256 of the files as published on npm (unchanged copies)
PINNED = {
    "assets/01_bootstrap-5.3.8.min.css": "d85327d99c7a3ee1f9b5d0500d1370acea3ad2db39c163c2f51f232baedbdede",
    "assets/fonts/source-sans-3-latin-wght-normal.woff2":
        "19143dca075972bc84e3fd9eab7416dd40cc565dccb2435a044bdfabe060c7d5",
    "assets/fonts/source-sans-3-latin-ext-wght-normal.woff2":
        "a85a7459bdb3cdc1136751e151a506bae653fc29ada3ca86237477df6f1b59e6",
}


@pytest.mark.parametrize("rel", sorted(PINNED))
def test_committed_vendor_files_are_the_pinned_upstream_files(rel):
    assert hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest() == PINNED[rel], (
        f"{rel} differs from the pinned upstream file: update it only together with this hash and D-044")


def test_licences_ship_with_the_vendored_files():
    for name, phrase in (("LICENSE-bootstrap.txt", "MIT License"), ("LICENSE-source-sans-3.txt", "SIL Open Font License")):
        assert phrase in (REPO_ROOT / "vendor" / "shell" / name).read_text(encoding="utf-8")


def test_no_old_bootstrap_and_no_third_party_styles():
    assert not (ASSETS / "bootstrap.css").exists() and not (ASSETS / "bootstrap.min.css").exists()
    for path in sorted(ASSETS.rglob("*.css")):
        text = path.read_text(encoding="utf-8")
        assert "@import" not in text, f"{path.name} imports another stylesheet"
        assert not re.search(r"url\(\s*['\"]?https?:", text), f"{path.name} loads something from another host"
    for runner in ("run_app.py", "run_app_dev.py"):
        src = (REPO_ROOT / runner).read_text(encoding="utf-8")
        assert "dbc.themes" not in src and "fontawesome" not in src.lower() and "font-awesome" not in src, runner
        assert 'data-bs-theme="dark"' in src, f"{runner} must put Bootstrap in dark mode"


def test_assets_load_in_order():
    """Dash includes assets/*.css in filename order: Bootstrap, then the font, the tokens, then the component styles."""
    names = sorted(p.name for p in ASSETS.glob("*.css"))
    assert names == ["01_bootstrap-5.3.8.min.css", "02_source-sans-3.css", "03_tokens.css", "04_shell.css",
                     "05_panel.css"]


def test_panel_styles_use_only_tokens():
    """The filter panel's styles take every colour from the tokens (3.12 step 3): no hex or rgb() colour values."""
    text = re.sub(r"/\*.*?\*/", "", (ASSETS / "05_panel.css").read_text(encoding="utf-8"), flags=re.S)
    values = re.findall(r":\s*([^;{}]+);", text)   # declaration values only, so #id selectors don't count
    assert not [v for v in values if re.search(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(", v)], "colour values outside the tokens"


# ---- contrast ---------------------------------------------------------------------------------------------------

def tokens():
    return dict(re.findall(r"(--st-[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\b", TOKENS.read_text(encoding="utf-8")))


def luminance(hex_colour):
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


TEXT = 4.5       # WCAG 1.4.3, normal text
NON_TEXT = 3.0   # WCAG 1.4.11, control borders and icons


@pytest.mark.parametrize("fg,bg,minimum", [
    ("--st-fg", "--st-panel", TEXT), ("--st-fg", "--st-bg", TEXT), ("--st-fg", "--st-raised", TEXT),
    ("--st-muted", "--st-panel", TEXT), ("--st-muted", "--st-raised", TEXT),
    ("--st-accent", "--st-panel", TEXT), ("--st-accent-hi", "--st-panel", TEXT),
    ("--st-on-accent", "--st-accent", TEXT),
    ("--st-warn", "--st-panel", TEXT), ("--st-error", "--st-panel", TEXT), ("--st-ok", "--st-panel", TEXT),
    ("--st-payload", "--st-panel", TEXT), ("--st-rocket", "--st-panel", TEXT), ("--st-debris", "--st-panel", TEXT),
    ("--st-active", "--st-panel", TEXT), ("--st-inactive", "--st-panel", TEXT),
    ("--st-control", "--st-panel", NON_TEXT), ("--st-control", "--st-raised", NON_TEXT),
])
def test_token_contrast(fg, bg, minimum):
    t = tokens()
    assert contrast(t[fg], t[bg]) >= minimum, f"{fg} on {bg}: {contrast(t[fg], t[bg]):.2f} < {minimum}"


def test_data_colours_are_d017s():
    t = tokens()
    assert (t["--st-payload"], t["--st-rocket"], t["--st-debris"]) == ("#56B4E9", "#E69F00", "#CC79A7")
