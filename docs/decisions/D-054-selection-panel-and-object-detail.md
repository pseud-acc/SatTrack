# D-054 Selecting a satellite: a sourced detail panel, the object_detail file, and search that follows the filters

**Status:** Accepted (owner, 28 Nov 2026, after trying each part on a laptop and a phone) · **Date:** 2026-11-28 ·
**PRs:** this PR (`feature/cesium-selection`)
**Component:** the globe's selection (`static/viewer/selection.js`, `viewer.js`, `worker.js`), the search list
(`assets/07_search.js`), the `object_detail` dataset (`app__object_detail.sql`, `app/contracts/object_detail.schema.json`)
· **Tier:** full for the data file (a new published contract), light for the UX choices
**Updates:** D-018 (tier 3 "More" in the list view becomes "More details" in the panel), D-019 (ground track drawn on
the globe until 3.5's 2D mode), D-024 (the hash carries version and satellite now), D-052 (a search pick on the globe
selects instead of filtering), D-010 (`object_detail`'s access).

## Context
Roadmap 3.4 was widened on 28 Nov 2026 for two audiences: children and casual visitors, and analysts and journalists
in comms, tech and space. The owner asked for richer object details (answer A), to try a search pick that selects
and flies (B) and a phone card (C) on a local test server before deciding, and every UX choice to be discussed first.

## Options and decisions

### The detail file: one fetch on the first selection (chosen) or one object at a time
| Option | For | Against |
|---|---|---|
| **The whole `object_detail` file, fetched by the worker on the first selection (chosen)** | Reuses D-012's delivery (pre-compressed, ETag, no new route); nothing new held in server memory beyond the compressed bytes; later selections are instant | The first selection downloads the file |
| A per-object route (`/data/object_detail/<id>.json`) | One small response per selection | Each worker parses the file at start-up and holds ~33k records (the 512 MB dyno); a new route to test |

**Measured** on the 28 Nov 2026 warehouse: 0.72 MB Brotli, 1.44 MB gzip, against the 8–15 MB D-012 estimated. So the
first selection costs less than the objects file itself, and the per-object route isn't needed. Fields: D-010's
agreed shape, plus `apoapsis`, `periapsis`, `rcs_size`, `owner_country_source`, `launch_agency_org_*`,
`operational_status_source` and `gcat_updated_at`, so every panel section can name its source and date. Same keys as
`objects` (the same GP scope), dates as ISO text beside their GCAT precision (every value the vague-date macro emits).

### The panel (owner's answers, 28 Nov 2026)
- A plain headline with exact values only (masses in kg, no comparisons): name, type and status (still operating /
  transmitting, with dates), owner, operator and manufacturer with roles, live height with the orbit type ("418 km ·
  Low Earth orbit (LEO)"), speed, the live longitude for a GEO object, launch, "one of N <constellation> (M active)".
- "More details": identity, organisations, launch, orbit, physical, status, group sections, each ending with its
  source and as-of date; uncertainty shown in place (estimated mass, approximate date, uncertain catalogue match) in
  the warning colour, a value's source in muted text.
- "Link" copies `https://www.sattrackapp.com/#v=1&sat=<satcat>`; "Cite" copies a one-line citation.
- Orbit, Ground track and Follow toggles (D-019); labels on the ~20 nearest objects when zoomed in (D-023), kept as
  they are on phones (owner).
- Controls: "–" minimises the panel to a pill with the satellite's name and keeps it selected; "×" clears it (the
  owner chose the window convention over a "Clear" label). Flat 36 x 24 px oblongs, with a larger touch target.
- On phones (C, chosen after trying it): a small card at the bottom (name, status, "436 km · LEO · 7.65 km/s",
  "More ▴") that expands; its bar drags it up and down (full card, small card, pill); the top (bar, name, – and ×)
  stays in view while the details scroll. Rejected: the full card at once (covered over half the globe), a grey
  "Details" button (looked like a stray box), a bar that couldn't be dragged.

### Search (owner's answers, 28 Nov 2026)
- B, chosen after trying it: on the globe a pick selects the object and flies to it, and the filters stay as they
  are, so what's around it stays shown; an object the filters hide is pinned (always propagated). On the 2D map and
  list tabs, which have no selection, a pick still filters to it (the 2D ground track).
- Option 3: browsing lists only what the filters show; typing searches everything, the globe's matches first, the
  rest under "Hidden by your filters". Rejected: the list following the filters strictly (a typed name could find
  nothing), type buttons inside the search (two places to choose a type).
- Option A: group headings with counts in the list's order and jump links ("Debris 10,125"). Rejected for now: a
  sort choice (doesn't help find junk). Space junk mode keeps the list's order (owner: switch Active off for junk).

## Evidence
`tests/e2e/test_selection.py` (selection, panel sources, live height/speed/longitude against Python sgp4 and a WGS84
conversion written in the test, toggles, shared and bad links, Link and Cite, search pick, search groups and hidden
objects, minimise and pill, the phone card's drag and pinned top, every panel control checked); the pipeline's
export tests (record shape, same keys as `objects`, vague-date precision); `tests/app/test_data_files.py` (the
sample follows the contract and is served).

## Consequences
- The pipeline publishes a third file each run; a contract violation keeps the last good files (as for `objects`).
- Until the first run after merge publishes `object_detail`, the panel shows the objects dataset's fields only.
- The satellite filter chip now appears only when a pick is made off the globe tab.

## Revisit when
- `object_detail` passes ~5 MB compressed (a per-object route becomes worth it).
- 5.1 adds GCAT's physical fields (additive to `object_detail`).
- 3.5 brings the 2D mode (the ground track moves there, D-019) and the full shareable hash (D-024).
- Visitors report the jump links or the hidden-objects divider as confusing.

## Related
D-009 to D-012, D-018, D-019, D-023, D-024, D-049, D-052, D-053; roadmap 3.4, 3.5, 3.9, 5.1, 5.2, 5.4.
