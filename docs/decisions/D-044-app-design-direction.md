# D-044 App design direction: deep navy, left filter panel, own design tokens on plain Bootstrap 5

**Status:** Accepted (owner, 2026-11-24) · **Date:** 2026-11-24 · **PRs:** #NN
**Component:** every app page: the Dash shell (`run_app.py`, `run_app_dev.py`, `assets/`, `app/layouts/`), the
tracker's filter panel and the Cesium viewer's chrome (`static/viewer/`) · **Tier:** full (changes every page)

## Context
The Cesium viewer (3.2) and its filter panel (3.3) are about to be built into the Dash shell, so this is the last
cheap moment to set how the app looks. An audit of the live site on 24 Nov 2026 found:

- **Two Bootstrap versions on every page.** Dash serves everything in `assets/` automatically, so each page loads
  `assets/bootstrap.css` and `assets/bootstrap.min.css` (an old Bootstrap 4.5 Cyborg build) as well as
  `dbc.themes.CYBORG` (Bootstrap 5.3 from the jsDelivr CDN, `run_app.py`, `run_app_dev.py`). They conflict.
- **Five accent colours:** cyan titles (`#00d4ff`), Bootstrap blue buttons and tabs (`#2a9fd6`), purple links, green
  and purple stats on the home page and a red Earth.
- White inputs on a black page; font sizes set inline in Python.
- The header pushes the viewer about 240 px down; the globe was 958 × 530 px in a 1366 × 900 window, its height
  copied from the Plotly figure's `calc(70vh - 100px)`.
- Filters don't say what they did: no match count, no summary of active filters, no "clear all".

The owner compared three looks (A neutral graphite, B deep navy, C light shell) and three filter layouts (F1 left
panel, F2 floating on the globe, F3 top bar) as mock-ups and screenshots on the design-directions page
(https://claude.ai/artifact/LKWAsxZ7s6oSrE5XuwufJu), and three build approaches.

## Options

**Look**

| Option | For | Against | Fit with planned features |
|---|---|---|---|
| A neutral graphite | Calm; no colour competes with the data | Flat; reads as a generic dashboard | Works with any "Colour by" palette (D-017, 3.13) |
| **B deep navy** | Blue-black chrome suits a globe in space; one teal accent (`#2bb3a3`) stays clear of the type colours (payloads `#56B4E9`, rocket bodies `#E69F00`, debris `#CC79A7`, D-017) | The accent must be checked against every new palette | Fits 3.13's palettes if the accent stays out of them; the detail panel (3.4) and bottom sheet (3.5) reuse the same tokens |
| C light shell | Familiar for documents and tables | Two themes to maintain (light chrome round a dark globe) | Doubles the styling work in 3.4, 3.5 and 2.4 |

**Filter layout**

| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **F1 left panel, collapsible to a thin strip** | Room for filters to grow; the globe stays uncovered; collapses when not needed | Takes width on small laptops (hence collapsible) | Phases 4–6 add filters (source, detail fields, plain-English query) without a redesign; phones keep the bottom sheet (D-025) |
| F2 floating on the globe | Globe takes the full window | Covers the globe | Gets worse as filters grow |
| F3 top bar | Full-width globe | Crowds as filters grow in phases 4–6 | Poor fit for Phase 5 and 6 filters |

**Build approach**

| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Plain Bootstrap 5 plus SatTrack's own `tokens.css`** | One Bootstrap; colours, type scale, spacing and radius in one file shared by the shell and the viewer; self-hosted font shortens the CSP (D-041 option E) | ~8–10 h now; every page needs a visual check | 3.3, 3.4 and 3.5 build straight onto the tokens; the viewer (`static/viewer/viewer.css`) reads the same variables |
| Keep Cyborg and override it | Least work today | Keeps the two-Bootstrap conflict and `!important` chains | Every later panel fights the theme |
| Switch component library (e.g. Mantine) | Modern components | Rewrites every layout | Delays Phase 3 by weeks |

**Tokens and assets** (owner, 24 Nov 2026, from the token sheet)

| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Font: Source Sans 3 (SIL Open Font License), self-hosted** | Open licence; reads well in panels and on the home page | One more file to ship (~100 KB) | Same face in the shell and the viewer overlays |
| Font: Inter | Most legible at small sizes (the recommendation) | Not the owner's choice | – |
| Font: IBM Plex Sans | – | A more technical feel | – |
| **Base size: 15 px in the app, 16 px for reading text** | Panels and controls stay compact; the home page reads comfortably | Two base sizes to keep straight | – |
| Base size: 14 px in the app | Denser panels | Small for casual visitors | – |
| **Ship Bootstrap 5.3 CSS (~230 KB) and the font by committing them under `assets/`, with a unit test pinning their SHA-256** | No CDN; the shell works with the viewer flag off | Two binary-ish files in the repo; upgrades by hand | Works however the viewer flag is set |
| Fetch them at build through `vendor/cesium.lock` | No committed copies | The shell would depend on vendor files whatever the viewer flag says; with the flag off the app must read no vendor files (commit f5cb0ba) | Ties the shell to the viewer's build step |
| **Icons: replace the ~10 Font Awesome icons with inline SVGs and drop Font Awesome's CDN stylesheet** | No third party on every page; shorter CSP | ~10 icons to redraw | – |
| Self-host Font Awesome | Icons unchanged | ~150 KB or more for ~10 icons | – |
| Keep the Font Awesome CDN | No work | A third party on every page | – |

## Decision

**Look: B "Deep navy".** Blue-black chrome, one teal accent `#2bb3a3` kept clear of the data colours (payloads
`#56B4E9`, rocket bodies `#E69F00`, debris `#CC79A7`, D-017), 6 px corners, hairline borders, no card shadows.

**Filters: F1, a left panel**, collapsible to a thin strip. Phones keep the bottom sheet (D-025). The panel works as
in the mock-ups:
- a live match count ("19,742 of 32,652 objects");
- changes apply at once (no Update button);
- object-type toggles with their colour swatches and counts, in the panel;
- segmented controls for status and orbit;
- "More filters" as rows that show their current value;
- active-filter chips with "Clear all";
- no "Clear Orbits" button: the orbit path is a toggle on the selection (D-019).

**Search must offer a browsable list as well as typing.** Users include children and casual visitors, so an empty
type-to-search box is not enough (PR #73 was closed for this reason). Any satellite search in the panel or the viewer
(3.9) also offers a list to browse.

**Build: plain Bootstrap 5 plus SatTrack's own `tokens.css`** (colours, type scale, spacing, radius), shared by the
Dash shell and the viewer. Remove `assets/bootstrap.css`, `assets/bootstrap.min.css` and `dbc.themes.CYBORG`.
Bootstrap 5.3's CSS and the font are committed under `assets/`, each pinned by a unit test of its SHA-256 (not fetched
through `vendor/cesium.lock`: with the viewer flag off the app reads no vendor files). Font Awesome's ~10 icons become
inline SVGs and its CDN stylesheet goes.

**Tokens** (from the token sheet; contrast measured against `--st-panel`):

| Token | Value | Use |
|---|---|---|
| `--st-bg` | `#0a1220` | page background |
| `--st-bar` | `#0c1526` | top bar |
| `--st-panel` | `#0d1729` | panels (the contrast reference) |
| `--st-raised` | `#111d33` | inputs, raised surfaces |
| `--st-hover` | `#16243f` | hover |
| `--st-line` | `#1d2a40` | hairlines (1.2:1, decorative only) |
| `--st-control` | `#55688c` | input borders (3.2:1) |
| `--st-fg` | `#dfe7f2` | text (14.4:1) |
| `--st-muted` | `#8b9ab3` | secondary text (6.3:1) |
| `--st-faint` | `#5f6f8a` | disabled only |
| `--st-accent` | `#2bb3a3` | the one accent (6.9:1) |
| `--st-accent-hi` | `#3cc9b8` | links, focus ring |
| `--st-on-accent` | `#04201c` | text on teal (6.6:1; white is only 2.6:1) |
| ok / warn / error | `#4cc38a` / `#f2c46b` / `#ff7a7a` | states |
| data colours | payloads `#56B4E9`, rocket bodies `#E69F00`, debris `#CC79A7` | unchanged (D-017) |

- Font: Source Sans 3 (SIL Open Font License), self-hosted.
- Type sizes 12, 14, 15, 16, 20 and 28 px; 15 px is the app's base (panels, controls), 16 px the reading size (home page).
- Spacing in 4 px steps; 6 px corners, pills for chips; no shadows; a 2 px teal focus outline.

**When:** a new roadmap task, 3.12 `feature/design-tokens-shell` (~8–10 h), before 3.3, so 3.3 builds the filter panel
straight into the new look (3.3 grows by ~2 h for the panel behaviour). 3.12 also takes the globe size: a compact top
bar, the globe filling the rest of the window, and a full-screen button.

## Evidence
- Audit of https://www.sattrackapp.com on 24 Nov 2026 (desktop 1366 × 900 and phone screenshots): the two Bootstrap
  builds, five accent colours, white inputs, inline font sizes, the ~240 px header offset, the 958 × 530 px globe and
  the filter panel without a match count, as listed under Context.
- Repo on `main`, 24 Nov 2026: `assets/bootstrap.css` and `assets/bootstrap.min.css` present; `dbc.themes.CYBORG` in
  `run_app.py` and `run_app_dev.py`; `calc(70vh - 100px)` in `app/layouts/components/visualizations/viz_3d.py`.
- Mock-ups of A, B and C, F1–F3 and the redesigned panel: the design-directions page
  (https://claude.ai/artifact/LKWAsxZ7s6oSrE5XuwufJu).
- The token sheet the owner reviewed on 24 Nov 2026 (https://claude.ai/artifact/WKZxuixmxgz1tHjWRe2S6D): the values,
  contrast ratios measured on `--st-panel`, the three fonts compared and the asset options.
- Commit f5cb0ba: with the viewer flag off the app reads no vendor files, which rules out fetching the shell's CSS and
  font through `vendor/cesium.lock`.
- Dash 4's `dcc.Dropdown` indexes every option in the browser: 2.2 s for ~32k options, measured 24 Nov 2026. A
  browsable search list therefore can't be a Dropdown with one option per object (see 3.9).

## Consequences
- 3.12 comes before 3.3 and adds ~8–10 h to Phase 3; 3.3 grows from ~4 h to ~6 h.
- Every page changes look in one release; 3.12 compares screenshots before and after for each page (home, tracker,
  list, about) at desktop and phone sizes.
- New colours come from `tokens.css` only; Python layouts stop setting inline font sizes and colours.
- The CSP loses the jsDelivr (Bootstrap theme), Google Fonts and Font Awesome hosts once 3.12 lands (D-041).
- ~330 KB of committed CSS and font; each Bootstrap or font upgrade updates the pinned SHA-256 in its unit test.
- A search feature without a browsable list doesn't meet this decision.

## Revisit when
- A "Colour by" palette (3.13) or a new data colour clashes with the teal accent.
- The filter panel can't show the planned filters (phases 4–6) in a collapsible column.
- Bootstrap 6 ships, or dash-bootstrap-components drops Bootstrap 5.
- Users ask for a light theme (option C).

## Related
D-016, D-017, D-019, D-025, D-041, D-045; roadmap 3.3, 3.9, 3.12, 3.13; PR #73 (closed).
