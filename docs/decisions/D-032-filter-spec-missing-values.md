# D-032 Missing values in the filter spec are explicit

**Status:** Accepted, 2026-11-22 (plan 2.2), by the owner. Settles the rule D-011 left open.
**Component:** `app/core/filter_spec.py`, the browser implementation (3.3), the sidebar.

## Context

The `objects` dataset keeps real nulls: 515 objects without an owner, 2 payloads without a launch year (D-011),
and objects with no mission labels. The legacy CSV replaced them with strings ("Unknown", status "Inactive"), so the
sidebar's "Unknown" option is a pipeline-made value. A spec must give the same answer in Python and in the browser,
where `null` comparisons differ by language unless the rule is written down.

## Options

| | Rule | For | Against |
|---|---|---|---|
| **A (chosen)** | A clause never matches a missing value unless it says so | One rule in both languages; "Unknown" becomes a real "no data" choice; nothing hidden by accident of a comparison | The sidebar must translate "Unknown" ↔ null |
| B | Copy the CSV: "Unknown" as a value | No translation now | Only possible with the CSV's names (rejected by D-030); the browser data has no "Unknown" strings |

## Decision

A scalar is missing when it is null; a list field when it is null or empty.

| Op | Missing values |
|---|---|
| `eq` | never match (`eq null` is invalid: use `is_missing`) |
| `in` | match only if the list contains `null` |
| `not_in` | the exact complement of `in` with the same list: missing values match unless `null` is listed |
| `between` | match only with `"include_missing": true` |
| `contains_any` | match only if the values contain `null` |
| `is_missing` | `true` selects only missing values; `false` only present ones |

`not_in` is the one operator where missing values match by default: making it the exact complement of `in` keeps
`in(L)` and `not_in(L)` partitioning the data, which people expect from "is" / "is not". Listing `null` excludes them.

In the UI, "Unknown" is shown for null and maps to `null` in the spec.

## Evidence

The shared conformance cases (`tests/contracts/filter_spec_cases.json`) pin every row of the table above, with
expected results worked out by hand.

## Revisit if

- Users find `not_in` keeping unknowns surprising (e.g. "not US" showing objects with no owner): add a sidebar
  hint, or make the sidebar add `null` to `not_in` lists by default.
