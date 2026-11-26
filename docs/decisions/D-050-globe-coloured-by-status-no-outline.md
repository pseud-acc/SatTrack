# D-050 The globe is coloured by status by default, with no point outline

**Status:** Accepted (owner, 24 Nov 2026; built in 3.3a) · **Date:** 2026-11-26 · **PRs:** this PR (`feature/cesium-filters`)
**Component:** the Cesium viewer's point styling, the design tokens · **Tier:** light
**Supersedes:** D-017's default (colour by type). **Updates:** D-022 (its provisional 1 px `#101010` point outline).

## Context
D-017 coloured points by object type by default, with a "Colour by" menu to come (D-045, roadmap 3.13). D-022 added a
provisional dark outline so points read on the natural-colour Earth, pending point-styling experiments. While choosing
the design (D-044, 24 Nov 2026) the owner reviewed the globe and decided the default colouring and point style.

## Options
| Option | For | Against |
|---|---|---|
| **Status: Active soft red, Inactive grey, no outline (chosen)** | Answers "is it working?" at a glance; today's app colours by status too; no teal on the globe (it clashes with the Earth) | Type is no longer shown by colour until 3.13's menu |
| Type (D-017) | Shows junk vs payloads | With payloads-only by default every point is the same colour |
| Keep the dark outline | Points read on bright land | The owner found it heavy; it darkens small points |

## Decision
Points take `--st-active` (#f07a6e) and `--st-inactive` (#7d8aa0) from the design tokens (`assets/03_tokens.css`),
read by the viewer at load, with no outline (`outlineWidth: 0`). Type colouring becomes an option of 3.13's
"Colour by" menu; the panel's type switches keep the D-017 swatches to name the types.

## Evidence
Owner's choice, 24 Nov 2026 (`~/.claude/plans/sattrack-3.3-decisions-2026-11-24.md`, "Colours"). Contrast: soft red
6.6:1 and grey 5.1:1 on the panel colour (`tests/app/test_design_tokens.py`). Browser test
`test_globe_opens_with_active_payloads_coloured_by_status` checks the colours the viewer uses.

## Consequences
- The red and grey are close in luminance (1.28:1) for colour-blind viewers, and both are 2.2–2.8:1 on the ocean;
  3.3b tunes this if needed (e.g. a darker or smaller inactive point).
- The swatches in the panel (type colours) differ from the points' colours (status) until 3.13.

## Revisit when
- 3.13's "Colour by" menu lands (the default may move with it).
- Colour-blind users report Active and Inactive as hard to tell apart.

## Related
D-017 (superseded default), D-022 (updated), D-044, D-045, D-048; roadmap 3.3a, 3.13.
