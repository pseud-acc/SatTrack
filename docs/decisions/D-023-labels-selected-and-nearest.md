# D-023 Label the selected satellite and, close up, the nearest 20

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the viewer · **Tier:** light

## Context
Thousands of labels cost frame rate; no labels leaves a crowded region (e.g. a Starlink shell) unreadable.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Selected always; the ~20 nearest when zoomed in** | Context when exploring, bounded cost | A nearest-N search per sample (in the worker) | Uses positions the worker already has |
| Selected only | Cheapest | No context | – |
| Selected + hovered | Cheap | Hover is already the tooltip | – |

## Decision
The selected satellite is always labelled. When zoomed in, the ~20 nearest objects are labelled too. N and the zoom
threshold are set within the budget (D-027).

## Evidence
The owner's call.

## Consequences
Labels are canvas text, not HTML, so names from the data can't inject markup.

## Revisit when
The budget can't absorb the labels' cost.

## Related
D-015, D-027.
