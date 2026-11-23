# D-016 Payloads by default; rocket bodies and debris one switch away

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the viewer · **Tier:** light

## Context
The `objects` dataset holds every tracked object (D-011). D-011 left the display defaults for debris and rocket
bodies to the spike.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Payloads by default; toggles for rocket bodies and debris; a "space junk mode" switch for both** | Clean first view; lighter first render on phones | The debris story is one click away | Re-entries and conjunctions turn junk on when needed |
| Payloads + rocket bodies | More context | Cluttered; no clear story | – |
| Everything except UNKNOWN | The full picture at once | Cluttered first view; heavier on phones | – |

## Decision
The globe opens with payloads (19,742). Rocket bodies (2,219) and debris (10,179) have their own toggles, and "space
junk mode" turns both on. UNKNOWN stays hidden (D-011).

## Evidence
The owner's call: use cases vary, and people should switch space junk on rather than be met with clutter.

## Consequences
Toggle state is part of shareable links (D-024). The slow-device hint (D-027) suggests switching debris off; it never
does so itself.

## Revisit when
Usage data shows most visitors switch junk mode on.

## Related
D-011, D-017, D-024, D-027.
