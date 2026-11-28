# D-059 The home page, the Explore pages, Sources and FAQ

**Status:** Accepted (owner, 28 Nov 2026, from three rounds of mockups and copy) · **Date:** 2026-11-28 ·
**PRs:** this PR (`feature/home-page`)
**Component:** the top bar (`layout_navbar`), the router (`run_app.py`), the home page (`layout_home`), the Explore,
Sources and FAQ pages (`layout_pages`), the start-up summary (`app/core/catalogue_summary.py`), `assets/06_home.css`
· **Tier:** full for the page structure and its claims, light for styling
**Builds on:** D-044 (design tokens, one font), D-047 (constellations and systems), D-054 (share links), D-056.

## Context
The old home page read as a hobby page and made claims the app couldn't back ("15,000+ satellites", pass prediction,
data export, "open source"). The owner wants a professional front door for two audiences (children and casual
visitors; analysts and journalists in comms, tech and space) that shows what's in the catalogue and where SatTrack
goes further. Mockups: https://claude.ai/artifact/A2sQWap72114XGryzuJp2t and
https://claude.ai/artifact/WbT3BKi74bz1j7oMTwfezs.

## Decisions (the owner's choices)
- **Top bar, option N2** ("less is more ... unambiguous"): Overview, Tracker, an Explore menu, Sources, FAQ. The
  menu lists a Summary and six views, each with one line saying what it is. Rejected: N1 (six tabs), N3 (a second
  row of tabs).
- **Hero copy**, settled word by word: "<N> tracked objects in Earth orbit." and "<M> working satellites, alongside
  inactive satellites, rocket bodies and debris. Explore them live on one globe, by owner, mission, constellation and
  orbit." N and M are read from the data. Tone rules from the owner: engaging but professional, informative but not
  overloaded; no "right now", "the rest", "dead", "defunct", "who is behind"; "tracked" keeps the claim true.
- **Catalogue summary, option S1**: six index tiles (one headline figure, the top three as plain numbers, one link),
  then a "From SatTrack's records" strip. Rejected: S2 (ranked tables with bars), S3 (question cards).
- **FAQ as its own page**; Sources as its own page.

## How it is built
- `build_summary()` counts the objects dataset (and object_detail, for operators and the records strip) once at
  start-up. Every figure on these pages comes from it; a test fails on typed-in claims the app can't back.
- The Explore menu needs destinations, so each view has a page: working satellites ranked by constellation,
  satellite system, operator, country, mission or orbit type (top 25, the rest counted). This brings forward the
  counts of roadmap 5.3.
- Quick links ("Go straight to") use D-054's share link and are offered only for objects present in the data.
- The FAQ's wording comes from the app's own definitions: the filter panel's orbit rules, D-047, D-053, GCAT's
  "believed to be still operating / transmitting".

## Deviations from the mockups
| Mockup | Built | Why |
|---|---|---|
| A search box in the hero | "Open the tracker", "Explore the catalogue" and quick links | The search list lives in the tracker and needs the globe to act on a pick; a home search belongs with roadmap 3.9 |
| Space Grotesk headings | Source Sans 3 throughout | D-044 keeps one self-hosted font; a second needs its own decision (files, hash test) |
| A "navigation systems" tile | "Satellite systems" | The data has no kind per system; the tile counts what the data has |
| Explore rows opening the tracker pre-filtered | Explore pages with a link to the tracker | Links that carry filters are roadmap 3.5 (the owner agreed to wait) |
| "Free and open source", "Coming next" | Left out | The licence is roadmap 3.7; no promises on the page |

## Evidence
`tests/app/test_catalogue_summary.py` (the counts, on hand-made records), `tests/app/test_pages.py` (every figure
against plain pandas over the sample; the agreed wording; every link leads somewhere; the FAQ's sources; no
unbacked claim), `tests/app/test_callback_navbar.py`, the journeys in `tests/e2e/test_journeys.py` (the menu, tiles,
FAQ, Sources; no sideways scroll on a phone). Start-up on the full 28 Nov data: 3.9 s with the summary.

## Consequences
- object_detail is parsed once at start-up for the counts and dropped; without it the operators view and the
  records strip are left out.
- The figures change with each data update (on redeploy, until roadmap 4.1's reload).

## Revisit when
- Roadmap 3.5 lands (Explore rows and tiles can open the tracker pre-filtered).
- Roadmap 3.7 lands (say "open source"); 3.9 (a home search box); 3.14b (definitions and sources per grouping on
  the Explore pages); 5.4 (Explore rows link to satellite pages).

## Related
D-044, D-047, D-053, D-054, D-056; roadmap 3.5, 3.7, 3.9, 3.14b, 5.3, 5.4.
