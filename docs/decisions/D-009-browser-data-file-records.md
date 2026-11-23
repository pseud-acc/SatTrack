# D-009 Browser data file: one record per object, with the warehouse's field names

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #57 (decision), #58 (plan 2.1)
**Component:** the `objects` dataset and its reader in the browser · **Tier:** full

## Context
From Phase 3 the browser propagates every tracked object itself (32,652 on 21 Nov). It needs one file holding each
object's OMM element set and the fields the filters use. Planned uses mix bulk work (propagating, filtering, grouping
all objects) with single-object work (click, detail panel, pass prediction, per-satellite pages, API).

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **One record per object, mart field names, under a header** | Each record stands alone: one bad value affects one object; every record can be schema-checked; any older file is a fallback | +0.33 MB Brotli and +26 ms (laptop) / +152 ms (4×) first load against columns | Click, detail panel, pass prediction, API, per-satellite pages are single-record work |
| One list per field with lookup codes | Smallest (1.61 MB gzip) | Codes couple two structures; a missing or reordered entry shifts values onto the wrong objects | – |
| One list per field, real names | Fast first load | Same alignment risk; single-record work needs a rebuild step | – |
| NDJSON | Streamable | Slower to parse (+17 ms laptop, +35 ms at 4×); no header for the count | – |

## Decision
Records sorted by `satcat_id` under a header (`schema`, `count`, `generated_at`, `run_id`). Field names are the dbt
mart column names, no renaming, no lookup tables; satellite.js's OMM names come from uppercasing the element fields'
names. The browser builds typed-array columns and an id index on load, in a Web Worker, never stored.

## Evidence
Warehouse of 21 Nov (32,652 objects, 27 fields), headless Chromium, best of 3:

| | records | columns, real names | NDJSON |
|---|---|---|---|
| Raw / gzip / Brotli | 23.7 / 2.44 / 1.70 MB | 8.8 / 1.63 / 1.37 MB | 23.7 / ≈2.44 / ≈1.70 MB |
| Parse + build columns, laptop / 4× CPU | 43 / 271 ms | 17 / 119 ms | 60 / 306 ms |
| Browser memory once loaded | 15.1 MB | 13.4 MB | 15.1 MB |
| Filter all objects, 4× CPU | 1.2 ms | 1.0 ms | 1.5 ms |
| Read one full record, 4× CPU | 8 µs | 27 µs | 13 µs |

## Consequences
The pipeline validates every record against a JSON Schema and checks count and unique, sorted ids. Lists are JSON
arrays (empty, not null). Element numbers are never rounded. Format in `docs/app-data-contract.md`.

## Revisit when
- The file passes ~5 MB Brotli (e.g. more fields or SupGP doubling records): re-measure first load at 4×.
- The Cesium spike's worker parses the file itself (3.1 confirmed this works: first positions in 1.0–1.7 s at 4–6×).

## Related
D-010, D-011, D-012; the Cesium architecture.
