# D-010 Data contracts: two core datasets, feature datasets, one envelope

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #57 (decision), #58 (plan 2.1)
**Component:** every dataset the app serves to the browser · **Tier:** full

## Context
Phases 3–7 add many browser features (Cesium viewer, detail panel, re-entries, conjunctions, events, history,
natural-language query). Without a common shape each would invent its own file format, names and freshness rules.

## Options
The full entry in [`../DECISIONS.md`](../DECISIONS.md#d-010-data-contracts-two-core-datasets-feature-datasets-one-envelope)
records the decision. Its option analysis, reconstructed:

| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Two core datasets (`objects`, `object_detail`) plus feature datasets, all in one envelope** | Each feature adds a dataset without touching the core; one validation and delivery path; real field names everywhere | More files to publish | Re-entries, conjunctions, events, history each get a feature dataset (see the dataset map in `docs/app-data-contract.md`) |
| One big file | One request | Every feature grows the first load | – |
| Per-feature formats | Freedom per feature | Repeated validation, naming and caching work; drift | – |

## Decision
See the log entry: two core datasets, feature datasets on demand, one envelope (`dataset`, `schema`, `count`,
`generated_at`, `run_id`, `key`, `attribution`, `caution`, `records`), warehouse field names with no mapping layer.

## Evidence
2.1 shipped the `objects` dataset this way: 32,652 records, every record validated, 1.69 MB Brotli.

## Consequences
Every dataset carries the Space-Track attribution and caution in its envelope. Display labels are not field names:
the filter spec decisions (2.2) add a dbt `meta.label` per column for what users see.

## Revisit when
- A feature needs a format JSON can't serve well (e.g. dense time series for orbit history): consider a binary
  feature dataset inside the same envelope rules.

## Related
D-009, D-011, D-012; `docs/app-data-contract.md`; filter spec decisions (2.2).
