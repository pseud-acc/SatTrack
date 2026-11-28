# D-055 The selection card's sections open on their own, and the tracker has a full-screen mode

**Status:** Accepted (owner, 28 Nov 2026) · **Date:** 2026-11-28 · **PRs:** this PR (`feature/card-sections-fullscreen`)
**Component:** the selection panel (`static/viewer/selection.js`), the viewer overlay and page layout in full screen
(`static/viewer/viewer.js`, `viewer.css`) · **Tier:** light
**Updates:** D-054 (one "More details" becomes sections that open on their own; a description line under the name).

## Context
After 3.4 went live (D-054) the owner compared the card and the tracker with KeepTrack's: it liked sections that open
one at a time and a short description of what the object is, and found the globe boxed inside the page on a laptop.
Design options: https://claude.ai/artifact/PbPynq3FcJVUCWxEg5pfyN (C1 to C3).

## Options
| Option | For | Against |
|---|---|---|
| **C2: each section opens on its own, remembered per visitor, with a description line (chosen)** | Scan the headings, open only what you need; a returning analyst finds their sections open | One more line under the name |
| C1: one "More details" (D-054) | Simplest | All or nothing: a long scroll to reach one section |
| C3: C2 with a summary line per section | Scannable without opening | Busier; the summaries repeat the headline |
| **Full screen: the tracker fills the window, filters as a drawer (chosen)** | The globe gets the whole screen on a laptop or phone; no new page or route | The panel moves into a drawer while in it |
| A separate full-screen page | Clean layout | A second tracker to keep in step |

## Decision
- **Sections:** Identity, Organisations, Launch, Orbit, Physical, Status and Group are each a `<details>` with the
  heading as its summary; which ones a visitor keeps open is remembered in the browser (`localStorage`
  `sattrack-open-sections`; a blocked store just forgets). Each keeps its source line.
- **Description** under the name, built only from the data: status and kind ("Active satellite", "Active space
  station"), GCAT's first mission category as GCAT writes it, and the operator (or first owner); for rocket bodies and
  debris, the kind and launch year. No hand-made phrases (the option's "data relay satellite" would have needed a
  mapping of GCAT's categories, against the published-definitions rule). The status line under it now carries only
  GCAT's operating and transmitting detail.
- **Full screen:** a "⛶ Full screen" button in the globe's status box puts a class on `<body>`: the tracker column is
  fixed over the window, the globe fills it below the tabs, and the browser's own full screen is requested where it
  is allowed (not on iPhones). A "Filters" button then opens the filter panel as a drawer below the status box,
  unfolded. Esc closes the drawer, then leaves full screen; leaving the browser's full screen leaves it too.

- **Globe controls** (owner, 28 Nov 2026, while trying full screen): "⌂ Reset view" in the status box flies back to
  the opening whole-Earth view, stops Follow and keeps the selection (the filters have "Clear all"); "+" and "−" on
  the globe's left edge zoom by 40% of the camera's height per press. The filter panel's "Filters" header and fold
  button stay in view while it scrolls, on the page (below the top bar) and in the drawer, which is one box with no
  border or gap of its own.

## Evidence
Owner's choices, 28 Nov 2026. `tests/e2e/test_selection.py`: sections open on their own and are remembered, the
description, full screen with the drawer (its controls still drive the globe; Esc), the phone drawer unfolded.

## Consequences
- The page's layout in full screen depends on the shell's classes (`.st-viz-col`, `.st-panel-col`, `#globe`): a shell
  change has to keep them or update `viewer.css`.
- Full screen isn't in the share link (D-024's hash); a shared link opens the normal layout.

## Revisit when
- The home page redesign makes the tracker a page of its own (it may become full-window by default).
- Visitors don't find the sections' headings (e.g. they never open any).

## Related
D-018, D-044, D-052, D-054; roadmap 3.4, 3.12.
