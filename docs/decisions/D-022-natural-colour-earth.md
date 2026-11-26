# D-022 Natural-colour Earth from self-hosted imagery

**Status:** Accepted (provisional) · **Date:** 2026-11-22 · **PRs:** #68 · **Point outline updated by D-050** (none)
**Component:** the viewer · **Tier:** light

## Context
Today's globe is a stylised greyscale Earth. Imagery must have clear free terms and, under D-014, no runtime third
party.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Natural Earth II, shipped with Cesium (public domain)** | No tile server; no account | Low resolution close up; blue points harder to read | Day/night lighting (D-028) works on it |
| Greyscale (saturation 0) | Points read clearly | Less inviting | A runtime setting: easy to switch |
| NASA GIBS tiles | Higher resolution | Runtime third party, against D-014 | – |

## Decision
Natural Earth II, self-hosted with Cesium. No external tile servers and no Cesium ion.

## Evidence
The owner's call, to revisit with point styling.

## Consequences
Point styling (size, outline, glow) has to keep points readable. Brightness and saturation are runtime layer
settings, so a muted look later is a small change or a user toggle.

## Revisit when
Point styling experiments in 3.2 (this record is provisional until then).

## Related
D-014, D-017.
