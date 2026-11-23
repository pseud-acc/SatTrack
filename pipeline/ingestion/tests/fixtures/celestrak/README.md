# CelesTrak group sample (test fixture)

The first three rows of seven CelesTrak GP groups, as CelesTrak published them on 22 Nov 2026 (CSV format, unchanged):
`starlink`, `oneweb`, `gps-ops`, `glo-ops`, `intelsat`, `ses` (included by the group config, D-026) and `gnss`
(excluded; its rows overlap `gps-ops`).

- **Source:** CelesTrak (Dr T.S. Kelso), https://celestrak.org/NORAD/elements/ ,
  `gp.php?GROUP=<group>&FORMAT=csv`. Constellation groups: CelesTrak (Dr T.S. Kelso).
- **Fetched by:** the `celestrak fetch` workflow on GitHub's runners (run 45061938995, 22 Nov 2026, 47 groups,
  no refusals), downloaded with `gh run download 45061938995 -n celestrak-groups`. Never fetched from a developer
  machine (D-008).
- **Orbital elements** in these rows originate from USSPACECOM via Space-Track.org. Public element sets must not be
  used for conjunction (collision) assessment.

Used by `pipeline/ingestion/tests/test_celestrak_groups.py`. The index page in those tests is **synthetic**: the
workflow's artifact held the group CSVs, not the index HTML, so the page's markup and the titles used there are
made up in CelesTrak's style ("GPS Operational") rather than copied from CelesTrak.
