# D-045 "Colour by" menu gets its own task straight after 3.3

**Status:** Accepted (owner, 2026-11-24) · **Date:** 2026-11-24 · **PRs:** #74
**Component:** roadmap Phase 3 (the Cesium viewer's legend and "Colour by" menu) · **Tier:** light (contained)

## Context
D-017 colours points by object type by default and asks for a "Colour by" menu (orbit class, status, owner,
constellation) with a legend. The roadmap scheduled only the constellation option (3.10); the other three options had
no task.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Its own task straight after 3.3** | The menu arrives with the filter panel's look (D-044); small, reviewable PR | One more task in the core | 3.10 then only adds constellation to an existing menu; 3.4's legend and selection reuse it |
| Fold into 3.10 | No new task | 3.10 is an extension and could be dropped; the core would ship without the menu D-017 asks for | Ties orbit class, status and owner to CelesTrak work they don't need |
| Fold into 3.3 | One PR for the panel | 3.3 is already growing (~6 h with D-044); too big for a 5-hour week | – |

## Decision
A new task, 3.13 `feature/cesium-colour-by` (~3 h), straight after 3.3: a "Colour by" menu with object type (default),
orbit class, status and owner, each with its legend. 3.10 then adds constellation to 3.13's menu.

## Evidence
D-017's record and `docs/ROADMAP.md` on 24 Nov 2026: only 3.10 mentions the menu, and only for constellations.

## Consequences
Phase 3 core grows by ~3 h. 3.10 depends on 3.13.

## Revisit when
- A colour mode needs data that isn't in the `objects` dataset yet (e.g. owner names longer than a legend can show).
- The legend gets too long to read for owner (many owners): may need a "top N + other" rule, decided then.

## Related
D-017, D-026, D-044; roadmap 3.3, 3.10, 3.13.
