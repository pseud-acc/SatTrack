# D-051 The filter panel shows its own state: count, segments, rows and chips

**Status:** Accepted (owner's 3.3 answers of 24 Nov 2026; details built in 3.3b) · **Date:** 2026-11-26 ·
**PRs:** this PR (`feature/filter-panel`)
**Component:** the filter panel (`app/layouts/components/filters/*`, `callback_filters.py`,
`helper__filter_display.py`, `assets/05_panel.css`) · **Tier:** light (contained in the panel; the spec is unchanged)
**Builds on:** D-044 (panel design), D-048 (one filter-spec store), D-049 (defaults).

## Context
D-044 set the panel's design: a live count, segmented controls, "More filters" rows showing their values, chips with
"Clear all", no Update button. The 24 Nov answers settled Q2 (hint when a shown type matches 0), Q3 (orbit
multi-select), Q4 (count on the server), Q6 ("matching / total"), Q8 (search S2) and Q10 (Clear orbits into Plotly 3D).
This record holds the details 3.3b had to choose while building it.

## Options
| Choice | Chosen | Rejected |
|---|---|---|
| Where the count, type counts, hints, chips and row summaries come from | One server callback over the **panel's control values**, through the same builder as the spec (`sidebar_filter_spec`); the type counts use the spec without its type clause | Reading the `filter-spec` store: it is `None` when no type or orbit is on, so the type counts and chips would have nothing to show exactly when they matter |
| Status control | One choice: **Active / Inactive / All** (the D-044 mock-up) | Two checkboxes (allowed "none", which selects nothing) |
| A chip's remove button | **Widens** its control (status All, every orbit, nothing selected, whole year range) | Back to the default (removing "Active" would do nothing) |
| The type chip | Shown, **no remove button** (the switches right above set it) | Removable (to what: every type is junk mode) |
| "Clear all" | Restores the **opening values** (D-049), shown only when something differs | Widens everything (would open on 32k objects) |
| "More filters" rows | Native **`<details>`** rows: open with no callback, keyboard and screen readers for free | Collapse components with a toggle callback per row |
| Chip removal, Clear all, junk mode | **One callback** owns these control outputs | A callback each, with `allow_duplicate` (the app test forbids a property set by two callbacks) |
| Launch-year bubbles | Removed: the row shows the range | Kept beside the row summary |

## Decision
As chosen above. Also: the type switches are the checklist's checkboxes drawn as switches on the right (still real
checkboxes); the panel note now reads "…only with status Inactive or All" since status is no longer checkboxes; the
2D map and list no longer have an Update button: they refresh on a filter or tab change (2D also on its timer).

## Evidence
3.3b on the sample: app tests (count, type counts and hints against plain pandas over the objects dataset; chip
removal; Clear all; search lists set once), browser tests (server count == browser match count after every change;
chips and Clear all drive the globe; rows open and close by keyboard), and `test_filter_change_cost` on the
full-size catalogue (figures in the PR).

## Consequences
- The count can never disagree with the spec: both come from the same values through the same builder.
- The list's positions are as of the last filter or tab change (no Update button). 3.6 retires the list's CSV path.

## Revisit when
- 3.14 adds group filters: they need a chip, a row and a place in `CONTROLS`.
- A chip's "widen" surprises people in testing (then: back to the default).

## Related
D-044, D-048, D-049; roadmap 3.3b, 3.6, 3.14.
