# D-024 Shareable links carry the core view in the URL hash

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #SPIKE
**Component:** the viewer · **Tier:** full (links outlive releases)

## Context
Links people share keep working for years, so the format is a public contract.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Core view in the hash: version, satellite, time, mode, colour mode, type toggles** | Small, easy to validate; never reaches the server | Camera and other filters not shared yet | Optional fields can be added without breaking links |
| Full state with camera | Exact reproduction | Bigger format to maintain | – |
| Short links stored on the server | Short URLs | Storage and abuse handling | – |

## Decision
The hash carries a format version, satellite, time, 2D/3D mode, colour mode and type toggles. The camera follows from
the selection. Each field is parsed against an allowlist, the hash is capped in length, nothing from it is written as
HTML, and location is never included. A time outside the ±1-day window shows "now" with a notice.

## Evidence
Decision rounds page (maintenance, security and legal notes), 22 Nov.

## Consequences
Check before release whether Google Analytics records the hash. Elements update daily, so positions can shift on a
later open.

## Revisit when
Users ask to share camera angles or filters.

## Related
D-016, D-017, D-019, D-020.
