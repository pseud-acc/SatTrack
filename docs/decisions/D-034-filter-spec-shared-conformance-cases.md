# D-034 One set of conformance cases for every filter spec implementation

**Status:** Accepted, 2026-11-22 (plan 2.2), by the owner. **Component:** `tests/contracts/filter_spec_cases.json`,
`tests/app/test_filter_spec.py`, the browser implementation (3.3).

## Context

The spec is applied in Python (the Dash sidebar, later NL query) and in the browser (Cesium, 3.3). Two
implementations of the same rules drift unless something holds them together. Missing values (D-032) are where
JavaScript and pandas differ most.

## Options

| | For | Against |
|---|---|---|
| **A (chosen): shared JSON cases** (records + spec → expected ids; invalid specs) | Both sides run the same file; adding a rule means adding a case once | The browser runner is extra work in 3.3 |
| B: Python tests only until Phase 3 | Cheaper now | The JS version gets written against prose, not cases |

## Decision

`tests/contracts/filter_spec_cases.json` holds 6 invented records (with null scalars, null and empty lists), 18
valid cases with hand-worked expected `satcat_id`s, and 17 invalid specs (unknown field or op, op not allowed for the
type, value outside the allowed values, wrong types, empty lists, extra keys, unknown version, too many clauses,
over-long strings). Two placeholders keep it short (`REPEAT_<n>`, `LONG_<n>`), expanded by each runner.

- `tests/app/test_filter_spec.py` runs every case against `app/core/filter_spec.py`.
- `pipeline/ingestion/tests/test_filter_spec_schema.py` checks every valid case passes the generated schema and
  every invalid one fails it, so the file stays meaningful for any implementation.
- Phase 3 adds a Playwright runner for the browser's implementation over the same file.

## Revisit if

- A bug is found in either implementation: add the case that would have caught it, before the fix.
