# D-049 The tracker opens on every active satellite; Space junk mode adds Inactive

**Status:** Accepted (owner, 26 Nov 2026) · **Date:** 2026-11-26 · **PRs:** this PR (`feature/cesium-filters`)
**Component:** the filter panel's defaults, Space junk mode · **Tier:** light
**Amends:** D-016 (the globe opens with payloads: now the *active* payloads). **Replaces:** the 24 Nov 2026 3.3
answer Q1 ("all payloads, any status").

## Context
Before 3.3a the panel opened on Active + LEO + GEO; the 24 Nov answer to Q1 was all payloads (any status, any orbit).
On 26 Nov, before 3.3a was built, the owner first kept Active + LEO + GEO, then chose every active satellite in any
orbit, so the MEO navigation systems (GPS, GLONASS, Galileo, BeiDou; D-047) show from the start.

Almost every rocket body and debris object is Inactive in the data (21 Nov catalogue: 2,219 and 10,179, all but 6
Inactive). With status Active, switching junk on would show almost nothing.

## Options
| Option | For | Against |
|---|---|---|
| **Active, every orbit; junk mode adds Inactive (chosen)** | Shows what works now, MEO systems included; junk mode does what it says | Status changes when the user only touched junk mode (visible in the panel) |
| Active + LEO + GEO (the old default) | No change for current users | Hides the navigation systems; junk mode shows nothing |
| All payloads, any status (24 Nov Q1) | Junk mode works without touching status | Opens on 19,742 points of which 3,166 are inactive; heavier Plotly 3D until 3.6 |
| Status applies to payloads only | Junk always shows | OR across fields: D-031's version-2 trigger |

## Decision
- The tracker opens on status **Active**, **every orbit class** (LEO, MEO, GEO, GSO, HEO), **payloads**, the whole
  launch-year range.
- **Space junk mode on** switches rocket bodies and debris on **and ticks Inactive** (Active stays as it was),
  remembering the status from before; **off** switches them off and restores that status.
- Ticking both junk types by hand turns the switch on, unticking either turns it off; neither changes the status.
  A junk type switched on alone does exactly that (24 Nov Q2): 3.3b's panel shows a hint when it matches 0 because of
  status.
- A note under the switches says it (owner, 26 Nov 2026): "Almost all rocket bodies and debris are inactive, so most
  show only with Inactive ticked. Space junk mode does this for you."

## Evidence
Sample (`tests/app_data`): 20 rocket bodies and 20 debris, all Inactive. Full catalogue, 21 Nov 2026: payloads 19,742,
16,576 of them Active (all with a launch year; 2 inactive payloads have none); rocket bodies 2,219 and debris 10,179,
6 of the 12,398 Active; earliest launch year 1958 for each type. Browser test
`test_panel_type_switches_and_space_junk_mode_filter_the_globe_without_reloading` checks debris alone (0 shown with
Active), junk on (every type, Active + Inactive) and off (back to active payloads) against plain Python.

## Consequences
- D-016's "opens with payloads (19,742)" becomes the active payloads (16,576 on the 21 Nov data).
- D-042's "records built before first positions == the payload count" still holds: records are built per type.

## Revisit when
- Usage data shows most visitors switch junk mode on (D-016's trigger).
- Many rocket bodies or debris gain an Active status in the data (today 6): the note and junk mode's status change
  would need rethinking.

## Related
D-016, D-032, D-047, D-048; roadmap 3.3a, 3.3b.
