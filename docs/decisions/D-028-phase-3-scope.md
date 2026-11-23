# D-028 Phase 3 scope: the core plus four extensions

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the roadmap · **Tier:** light

## Context
The review listed extensions beyond the roadmap's 3.2–3.6. PNG export was the one feature that would be lost.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Core plus search and fly-to, save image (PNG), constellation colouring, day/night with shadow dimming** | Fills the gap the review found; uses data in hand | Phase 3 grows to ~55–65 h | Shadows lead into WASM (D-029) |
| Core only | Smallest | Loses PNG export | – |
| Core plus more (passes, footprints) | Richer | Belongs with Phase 7's observer features | – |

## Decision
Phase 3 is the core (3.2–3.6 and D-013 to D-027) plus four extensions, split into core and extension tasks in the
roadmap and re-estimated at ~55–65 h.

## Evidence
The owner's call.

## Consequences
Constellation colouring waits for the pipeline task adding `constellation` (D-026). Shadow dimming triggers the WASM
switch (D-029).

## Revisit when
The core runs over its estimate: move extensions to a later phase.

## Related
D-021, D-026, D-029; roadmap Phase 3.
