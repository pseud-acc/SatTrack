# D-017 Colour by object type, with a "Colour by" menu

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #68
**Component:** the viewer · **Tier:** light

## Context
Today's app colours payloads Active / Inactive. With every object type on the globe (D-011, D-016), colour has to make
the type toggles readable and keep today's views.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **By type by default; a menu for orbit class, status, owner, constellation; a live legend** | Matches the toggles; keeps today's owner and status views | A legend component to build | Constellation colouring (D-026) slots into the menu |
| Type only | Simple | Loses today's views | – |
| Orbit class by default | Shows orbital structure | Doesn't match the toggles | – |

## Decision
Points are coloured by type by default. A "Colour by" menu switches to orbit class, status, owner or constellation, and
the legend follows it.

## Evidence
The owner's call; constellation was the owner's addition.

## Consequences
Constellation colouring needs the `constellation` field (D-026). The palette must work on natural colour (D-022) and be
colour-blind safe.

## Revisit when
Point styling work (D-022) shows a colour can't stay readable on the chosen Earth.

## Related
D-016, D-022, D-026.
