# D-031 Filter spec shape: a versioned flat AND list of clauses

**Status:** Accepted, 2026-11-22 (plan 2.2), by the owner. **Component:** `app/contracts/filter_spec.schema.json`,
`app/core/filter_spec.py`, the browser implementation (3.3), natural-language query (Phase 6).

## Context

The spec must express every sidebar control today and be the safety boundary for NL query later: a model turns a
question into a spec, the app validates it against the schema, and only then runs it. What the shape can express
decides what NL query can answer; what it can't express can't be abused.

## Options

**A (chosen): flat list, version 1.**
`{"version": 1, "clauses": [{"field", "op", "value"}, ...]}`, every clause must hold. Operators: `eq`, `in`,
`not_in`, `between`, `contains_any`, `is_missing` (by field type). OR within one field is `in` /
`contains_any`; NOT within one field is `not_in`.

**B: nested boolean tree now.** `{"all": [...]}`, `{"any": [...]}`, `{"not": {...}}` nodes around the same clauses.

## Against future features

| Feature | Example | A: flat list | B: tree |
|---|---|---|---|
| Every sidebar control | status, orbit, owner, vehicle, purpose, year, name, id | ✅ | ✅ |
| OR within a field | "Starlink or OneWeb" | ✅ `in` | ✅ |
| OR across fields | "Chinese satellites **or** anything in GEO" | ❌ (two queries, or not supported) | ✅ `any` |
| Negation of a group | "not (inactive and launched before 2000)" | ❌ | ✅ `not` |
| Negation of one field | "not owned by the US" | ✅ `not_in` | ✅ |
| Missing values | "owner unknown" | ✅ (D-032) | ✅ |
| Near / geographic | "over the UK now", "within 500 km of the ISS" | ❌ needs new ops either way | ❌ needs new ops either way |
| Time-relative | "launched in the last 30 days", "re-entering this week" | ❌ needs a relative value type either way (e.g. `{"days_ago": 30}`) | ❌ same |
| Ranking and limits | "the 10 highest", "newest first" | ❌ not a filter: a separate `sort` / `limit` part of the query | ❌ same |
| Counting / grouping | "how many per country" | ❌ a separate aggregate request | ❌ same |

Most gaps are new operators or a separate query part, not the shape: A and B need the same additions for geo,
relative time, ranking and grouping. Only OR across fields and grouped negation need B.

| | A: flat list | B: tree |
|---|---|---|
| Validation | One JSON Schema `oneOf` per field; easy to read and audit | Recursive schema; needs depth and node-count limits |
| Safety surface for NL query | Small: a spec can only narrow, clause by clause, max 32 clauses | Larger: depth bombs, huge `any` fan-outs, harder-to-explain results |
| Showing the filter back to people | A list of chips ("Status: Active", "Owner: France") | Needs a tree view or nested sentences |
| Two implementations (Python, browser) | ~80 lines each; shared cases cover it | Recursion, short-circuit rules, more cases |
| Sidebar mapping | One clause per control | Same, wrapped in `all` |
| Upgrade path | Version 2 can add a tree; version 1 specs stay valid as `{"all": clauses}` | Already there |

## Decision

A, with `version: 1` required, so a tree can come later without breaking stored or shared specs.

## Triggers for a version 2 (nested tree)

Revisit when any of these happens:
1. NL query (Phase 6) logs show **≥ 5% of questions need OR across fields or grouped negation**, measured on
   real queries over at least two weeks.
2. A **UI feature needs OR across fields**: saved views combining selections ("my watchlist **or** anything
   launched this week"), or Cesium layers that union two filters.
3. **Shareable links (D-024 in the Cesium review) need to carry such a selection.**

When adding geo, relative-time, ranking or grouping, add them as new operators or a separate query part in
version 1 (or 2): they don't by themselves justify a tree.

## Consequences

- NL query can answer "A and B and C" questions directly; OR-across-fields questions get a clear "can't combine
  those yet" answer, or run as separate queries shown side by side.
- `version` is checked; an unknown version is rejected, never guessed.
