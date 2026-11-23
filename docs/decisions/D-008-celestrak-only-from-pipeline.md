# D-008 Fetch CelesTrak data only from the pipeline; never retry a refusal

**Status:** Accepted · **Date:** 2026-11-21 · **PRs:** #55
**Component:** plan 4.2 SupGP ingest; any CelesTrak download · **Tier:** full

## Context
CelesTrak blocked the owner's home IP after old local scripts (no longer run) fetched too often. Plan 4.2 adds SupGP,
which CelesTrak publishes. GitHub's runners share IP addresses with other users.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Pipeline on GitHub Actions only; one download per group per CelesTrak update; bulk files; stop on refusal** | Can't make the block worse; GP keeps the app working | Local development can't fetch CelesTrak directly | SupGP (4.2); the on-demand fetch workflow (#62) applies the same rules for analysis |
| Local fetching with care | Convenient | The owner's IP is blocked; any slip prolongs it | – |
| Retry with backoff on 403/429 | Rides out transient refusals | Retrying a refusal is what gets IPs blocked | – |

## Decision
Only the pipeline on GitHub Actions downloads SupGP: each group at most once per CelesTrak update, using the bulk
files. A 403, a 429 or an HTML body means "no SupGP this run": keep GP and don't retry. Warn only after 3 refused days
in a row, because runner IPs are shared.

## Evidence
The block itself (not lifted as of 22 Nov 2026).

## Consequences
Local testing uses data fetched remotely (the on-demand workflow in #62 uploads a short-lived artifact). Republishing
CelesTrak's compiled data, such as group lists, needs a terms check first (CLAUDE.md).

## Revisit when
- CelesTrak lifts the block or publishes an API with documented limits.
- SupGP refusals exceed the 3-day warning repeatedly.

## Related
Roadmap 4.2; the constellation source decision (Cesium decisions, GCAT first).
