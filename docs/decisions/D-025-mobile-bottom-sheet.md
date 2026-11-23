# D-025 Bottom sheet on phones

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the tracker page · **Tier:** light

## Context
Today's collapsible sidebar covers the globe on phones.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **One bottom sheet: peek (time, Now), half (filters or the selection), full (details)** | Globe gets the whole screen; thumb reach; a known pattern | A new component (~2 days); two layouts to keep in step | Holds D-019's toggles |
| Today's collapsible sidebar | No new work | Covers the globe | – |
| Floating buttons with overlays | Flexible | Several overlays to manage | – |

## Decision
On phones the globe fills the screen and one bottom sheet holds time (peek), filters or the selected satellite (half)
and details (full). Desktop keeps the sidebar.

## Evidence
The owner's call.

## Consequences
Playwright tests at phone sizes. Both layouts share the same Dash components.

## Revisit when
–

## Related
D-018, D-019.
