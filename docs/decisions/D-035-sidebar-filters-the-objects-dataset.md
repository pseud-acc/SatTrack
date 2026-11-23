# D-035 The server's sidebar filters the objects dataset; no fallback

**Status:** Accepted, 2026-11-22 (plan 2.2), by the owner. **Component:** `app/core/state.py`,
`app/core/filter_spec.py` (`table_from_dataset`), `app/helper/helper__app_data.py` (`filter_satellite_data`).

## Context

The filter spec uses the `objects` dataset's field names (D-030). Until plan 3.6 the Plotly views, list view and
dropdowns still work from the app CSV (`satcat_tle.csv`), whose headers (`Status`, `Owner`, `Purpose`) and values
("Unknown", "/"-joined lists) differ. The server needs a table in the spec's vocabulary to run the sidebar's spec on.

## Options

| | How | For | Against |
|---|---|---|---|
| **A (chosen)** | Build a filter table from the `objects` dataset at start-up; select the CSV rows by `satcat_id` | No name mapping anywhere (D-010, D-030); the server filters the same data the browser will (3.3) | Start-up cost per worker; the app can't start without `objects.json` |
| B | Rename the CSV's columns to the spec's names in one function ("Unknown" → null, "/" → list), deleted with Plotly in 3.6 | No start-up cost, no new dependency on `objects.json` | A temporary mapping layer, the kind D-010/D-030 avoid; two vocabularies until 3.6 |
| C | A, falling back to B while `objects` is missing | Deployable any time | Both code paths until 3.6; a silent fallback hides a broken publish |

## Measurements

Building the table from the full export of 21 Nov 2026 (32,652 records, 1.70 MB Brotli / 2.44 MB gzip), on a
laptop, Python 3.12, `tracemalloc`:

| | |
|---|---|
| Decompress + parse | **0.86 s** |
| Memory after parsing | 58 MB |
| Peak while building the table | **~81 MB** |
| Kept after start-up (the table) | **~15 MB** (13 MB deep size of the 9-column frame) |

Per gunicorn worker, once, at start-up (2 workers on 512 MB dynos). The peak is transient: the parsed document is
dropped as soon as the table exists.

In the CI sample, 339 of the 341 CSV satellites are in the sample `objects` dataset and match on all 7 filter fields
compared; the other 2 decayed between the two sample runs. In production both files come from the same run, and the
CSV's rows are a subset of the dataset's (the CSV needs a GCAT match and a launch year on top of the same full
element set).

## Decision

A. At start-up the app builds the filter table from the gzip copy of `objects`, checks its envelope (name, count)
and logs its size and how many CSV satellites it lacks. If the dataset is missing, unreadable or fails the check,
start-up stops with a `FATAL` line in the log: no fallback. CI's Heroku-identical build check runs the app on the
sample (which has the dataset), so a missing dataset fails the build check too.

**Deployment order:** merge only after production has published `objects.json` (the first is the 23 Nov 2026
03:17 UTC run), verified live at `/data/objects.json`.

## Consequences

- A pipeline publish without `objects` would stop new app releases from starting; the running release keeps working
  (Heroku keeps the old dynos until new ones boot). The pipeline already publishes both files from one run.
- The sidebar's "Unknown" and "Inactive" behave exactly as before: "Unknown" is a missing value, "Inactive" also
  covers objects with no status (D-032; the CSV filled those with "Inactive").
- Plan 3.6 removes the CSV path; the filter table stays (NL query and the list view use it).

## Revisit if

- Memory on the dyno gets tight (Heroku R14): keep only the filter columns while streaming the JSON, or build the
  table in the pipeline as a small extra file.
- `objects` grows a lot (e.g. `catalogue_history`-sized): measure again.
