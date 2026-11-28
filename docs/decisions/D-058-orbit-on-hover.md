# D-058 Resting the pointer on a dot draws its orbit

**Status:** Accepted (owner, 28 Nov 2026) · **Date:** 2026-11-28 · **PRs:** this PR (`feature/orbit-on-hover`)
**Component:** the globe's hover label (`static/viewer/viewer.js`) · **Tier:** light
**Builds on:** D-018 (hover is the first information tier), D-019 (the selection's Orbit toggle), D-052 (hover labels).

## Context
Comparing with other trackers (28 Nov 2026), the owner liked seeing an object's orbit by pointing at it, without
selecting it, and asked for it straight after the List View work.

## Options
| Option | For | Against |
|---|---|---|
| **Draw after a 300 ms rest, desktop pointers only (chosen)** | Sweeping the pointer across thousands of dots draws nothing; cheap (one worker call, the selection's orbit code) | A short wait before the line shows |
| Draw at once on every hover | Immediate | Flickers lines while the pointer crosses the globe; a worker call per dot passed |
| On touch screens too (tap) | Same on phones | A tap already selects, and the card has an Orbit toggle |

## Decision
When the hover label shows for an object and the pointer stays for 300 ms, the worker's orbit track (one period, in
the Earth-fixed frame of now, as the Orbit toggle draws it) is drawn as a thin line in the text colour at 55%. It
goes when the pointer leaves the dot, the camera moves, or the object is clicked. Not on devices without hover
(`(hover: none)`), and not for the selected object while its own orbit is on. The line is static, so there is no
animation for `prefers-reduced-motion` to switch off.

## Evidence
`tests/e2e/test_selection.py`: the orbit shows after the rest (not at once) for the object under the pointer, with
about 180 points, and goes when the pointer leaves; a brief pass draws nothing; nothing on a touch screen.

## Consequences
- One more worker call per rested hover; nothing while the pointer moves.

## Revisit when
- "Colour by" (3.13) lands: the hover line may take the object's colour.
- Visitors find 300 ms too slow or too quick.

## Related
D-018, D-019, D-052, D-054; roadmap 3.16.
