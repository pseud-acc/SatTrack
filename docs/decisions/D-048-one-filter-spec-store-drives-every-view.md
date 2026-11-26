# D-048 One filter-spec store drives every view; the browser filters in the worker

**Status:** Accepted (owner, 24 Nov 2026; built in 3.3a) · **Date:** 2026-11-26 · **PRs:** this PR (`feature/cesium-filters`)
**Component:** the filter panel, the Cesium viewer and its worker, the Plotly 3D/2D and list callbacks ·
**Tier:** full (shapes every later panel and viewer feature)

## Context
Roadmap 3.3 makes the left panel drive the Cesium globe. Before it, each Plotly view took the panel's eight control
values and built its own spec, and the globe ignored the panel (it had its own type toggles). The scope
(`~/.claude/plans/sattrack-scope-3.3.md`) put eleven questions to the owner on 24 Nov 2026; this record holds the
architectural answers (Q4, Q5, Q7, Q8, Q9, Q10, Q11). The defaults are D-049, the colouring D-050.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **One page-level `filter-spec` store, built in Python; every view reads it; the worker masks (chosen)** | One builder (no second spec builder without conformance cases); every view agrees; filtering off the main thread; no data reload | One server round trip per change (~50–150 ms) | Count, chips and row summaries (3.3b) read the same spec; NL query (Phase 6) writes it |
| Build the spec in JavaScript | No round trip | A second builder with no conformance cases (D-034 covers evaluation, not building) | — |
| Keep the eight inputs on each Plotly callback | Less churn in files 3.6 deletes | Three copies of the input list; control shape changes ripple through each | — |
| Filter on the main thread | Simpler | Main-thread time per change grows with 32k objects (D-027) | — |
| Vendor Ajv for validation in the browser | Full JSON Schema | Its compiler uses `new Function`, which D-041's policy (no `'unsafe-eval'`) blocks; adds to `vendor/cesium.lock` | — |

## Decision
- **Store (Q7).** A page-level `dcc.Store("filter-spec")`. A server callback (`update_filter_spec`) turns the panel's
  controls into one validated spec (D-031). The page renders the starting spec into the store
  (`prevent_initial_call`), so the globe masks before its first samples with no round trip (D-042). Plotly 3D, 2D and
  the list read the store instead of the controls.
- **Types (Q5).** Payloads, rocket bodies and debris are panel switches and an `object_type in [...]` clause; "Space
  junk mode" is a panel switch (D-016). UNKNOWN is never offered. The globe's overlay keeps only its status line, the
  slow-device hint and the credits.
- **Browser implementation.** `static/viewer/filter_spec.js` evaluates and validates specs with no imports and no
  eval. Its rules (`browser_rules()`: version, clause limit, per field its kind and each operator's value schema) come
  from the generated schema in the viewer config (4 KB, 443 bytes gzipped), so nothing is copied by hand. It passes
  every case in `tests/contracts/filter_spec_cases.json` in headless Chromium (`tests/e2e/test_filter_spec_browser.py`).
- **Worker.** Keeps each object's nine filterable fields, builds a `Uint8Array` mask per spec, propagates masked-in
  objects only, and reports matched counts per type. A new spec never reloads the data or recreates the worker.
- **Search dropdowns (Q8), for 3.3b.** S2: today's two lists, set once at load. In 3.3a the dropdown callback keeps
  its own control inputs (it writes the name and SATCAT values that feed the store, so reading the store would make a
  callback cycle).
- **Count (Q4), for 3.3b.** Computed on the server from the spec; the browser's count is checked against it in tests.
- **Clear Orbits (Q10), for 3.3b.** Moves into the Plotly 3D tab until 3.6.
- **Flag (Q9).** Switched on at the end of 3.3b with the Heroku config var `SATTRACK_CESIUM_VIEWER` (owner's go-ahead
  at the time); 3.6 makes it the code default.
- **Split (Q11).** 3.3a `feature/cesium-filters` (this record), 3.3b `feature/filter-panel`.

## Evidence
3.3a, 26 Nov 2026, sample data: app tests 274 passed; browser tests 51 passed (35 conformance cases, exact shown ids
against plain Python over the sample for the start view, debris alone, junk mode on and off and an orbit change; one
`objects.json` request and the same canvas after every change). D-042 against `main` on the full-size catalogue (local
laptop): every start-up phase +4–6 % (limit: over 20 % and over 150 ms), bytes before first positions 4.04 → 4.05 MB,
records built before first positions = the payload count.

## Consequences
- Until 3.6 the globe shows every object type from `objects`, while Plotly and the list show the app CSV's payloads:
  their counts differ, and with payloads switched off those views are empty.
- The server and the browser each implement the spec; any bug found gets a conformance case first (D-034).
- The launch-year slider starts on its whole range (1958 to this year), not the app CSV's, so older rocket bodies and
  debris aren't hidden by default. Objects with no launch year stay outside any `between` range (D-032): 2 inactive
  payloads in the 21 Nov catalogue.

## Revisit when
- A filter change's round trip is noticeable (3.3b's filter-change budget test reports it).
- D-031's version-2 triggers fire (OR across fields): the browser validator then needs `oneOf`/nesting.
- The CSV path goes (3.6): Plotly/list differences disappear.

## Related
D-016, D-017 (superseded default), D-030–D-035, D-041, D-042, D-049, D-050; roadmap 3.3a, 3.3b, 3.6.
