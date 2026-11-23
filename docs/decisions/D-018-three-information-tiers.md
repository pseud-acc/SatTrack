# D-018 Three information tiers: hover, click panel, full record

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #68
**Component:** the viewer and the list view · **Tier:** light

## Context
Plotly gave a rich hover label for free; Cesium has picking but no hover labels, and picking one of 32,000 points reads
back from the GPU.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Three tiers: hover (name, type, orbit, owner), click panel, "More" → list view** | Keeps today's quick look; adds the missing click panel; touch gets it by tap | Picking throttled to ~20 a second | The panel reads `object_detail` (3.4) |
| Two tiers: full hover label, click opens the panel | Fewer components | Heavy hover; nothing on touch | – |
| Panel only | Simplest | Loses today's quick look | – |

## Decision
Hover: name, type, orbit, owner. Click: altitude, speed, period, element age at the displayed time, launch. "More"
opens the full record in the list view. A tap replaces hover on touch screens.

## Evidence
Review of today's features (decision rounds page, 22 Nov).

## Consequences
Every data string is written with `textContent`, never HTML; Cesium's InfoBox stays off.

## Revisit when
Picking cost shows in the budget (D-027) at a larger catalogue.

## Related
D-019, D-025, D-027.
