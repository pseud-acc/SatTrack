# CelesTrak test fixtures

Source: CelesTrak (Dr T.S. Kelso), https://celestrak.org/ . Constellation groups: CelesTrak (Dr T.S. Kelso).
Everything here was downloaded by the `celestrak fetch` workflow on GitHub's runners and taken from its artifact;
nothing was fetched from a developer machine (D-008).

## Group CSVs (`<group>.csv`)

The first three rows of seven CelesTrak GP groups, as CelesTrak published them on 22 Nov 2026 (CSV format, unchanged):
`starlink`, `oneweb`, `gps-ops`, `glo-ops`, `intelsat`, `ses` (included by the group config, D-026) and `gnss`
(excluded; its rows overlap `gps-ops`).

- **URL:** `https://celestrak.org/NORAD/elements/gp.php?GROUP=<group>&FORMAT=csv`.
- **Fetched by:** run 45061938995 (22 Nov 2026, 47 groups, no refusals), downloaded with
  `gh run download 45061938995 -n celestrak-groups`.
- **Orbital elements** in these rows originate from USSPACECOM via Space-Track.org. Public element sets must not be
  used for conjunction (collision) assessment.

## GP index page (`gp_index_2026-11-23.html`)

A trimmed copy of CelesTrak's GP index page ("NORAD GP Element Sets Current Data"), https://celestrak.org/NORAD/elements/ ,
as served at 2026-11-23 02:17 UTC (HTTP 200) to run 45099334610 (the fetch workflow in pages mode). Only the page's
lines 140-226 are kept: the layout table holding the seven group tables (section headings, group titles, and the
`gp.php` / `table.php` links), which is all `sattrack_ingest/celestrak.py` parses. Unchanged otherwise.

Used by `pipeline/ingestion/tests/test_celestrak_groups.py`. Download tests that need a smaller index build one in the
same markup.
