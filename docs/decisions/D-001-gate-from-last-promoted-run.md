# D-001 Count the 12-hour gate from the last promoted run

**Status:** Accepted · **Date:** 2026-11-20 · **PRs:** #48
**Component:** pipeline state (`infra/state/sattrack_state.py`), the run gate · **Tier:** light

## Context
The pipeline refuses to start within 12 hours of the previous run, to protect the Space-Track quota (GP at most once
an hour; the daily schedule is the normal case). The gate counted from `last_ok_at`, which moves only when a run ends
**ok**. From 16 Nov every run ended in **warn** (GCAT enrichment held by duplicate JCATs, D-002), so the gate never
blocked and back-to-back manual runs could call Space-Track GP again within hours.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| Count from the last **promoted** run (ok or warn) | Spaces runs whenever new data went live, whatever the status | A new manifest key, with a fallback for old manifests | Plan 4.1 (several runs a day) lowers the gate deliberately; the same key works |
| Keep counting from the last ok run | No change | Fails open while runs warn, exactly the case that happened | – |
| Count from the last attempted run | Strictest | A failed or crashed run would block the retry that fixes it | Works against unattended recovery |

## Decision
`push` records `last_promoted_at` whenever the build goes live (ok or warn); `pull` gates on it, falling back to
`last_ok_at` for manifests written before the key existed. Error, crash and integrity-held runs move neither key.
`--force` still skips the gate for manual runs.

## Evidence
State-script tests 25 → 28: a warn run 3 h ago blocks even though the last ok run was 27 h ago; the fallback skips at
3 h and runs at 12.1 h. Mutation checks: gating on `last_ok_at` only fails 3 tests; not recording the key fails 2.

## Consequences
The gate protects the quota whenever data changes. Messages say "a run's data went live" rather than "a successful
run".

## Revisit when
- Plan 4.1 moves to several runs a day: lower the gate (`--min-hours`) as a deliberate, owner-approved change.
- A run status is added between warn and error.

## Related
D-002 (the warn runs that exposed this), roadmap 4.1.
