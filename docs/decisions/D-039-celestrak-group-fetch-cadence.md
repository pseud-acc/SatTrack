# D-039 CelesTrak groups: at most once a day, and no request for 20 hours after a refusal

**Status:** Proposed (owner to confirm) · **Date:** 2026-11-23 · **PRs:** `feature/constellation-field` (plan 3.8)
**Component:** `pipeline/ingestion/sattrack_ingest/celestrak_groups.py`, `config.py` (`CELESTRAK_MIN_HOURS`,
`CELESTRAK_REFUSAL_COOLDOWN_HOURS`); reused by SupGP (plan 4.2) · **Tier:** light (two constants; easy to change back)

## Context
D-026 says "once per update" and "wait 15 minutes after a 5xx"; D-008 says never retry a refusal and warn only after
3 refused days. Neither says how often the daily pipeline should download the groups, or what "never retry" means
across runs. CelesTrak's usage policy (16 Nov 2026): GP updates every 2 hours; download once per update; stop on any
non-200 and "report the results to a human"; after a 500/503 stop all requests for at least 15 minutes; directory
queries no more than once per hour. Group membership changes slowly (launches, retirements). The pipeline runs once a
day today (03:17 UTC) and may run several times a day after plan 4.1. The owner's home IP is already blocked, and
GitHub's runners share IPs with other users.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| Every run, at most once per 2-hour update | Freshest membership | Up to 12 x 21 requests a day after 4.1, including the large Starlink list CelesTrak is starting to limit; no gain for slowly changing membership | – |
| **At most once per 20 hours (age of the landed copy); after any refusal, no request for 20 hours** | One download a day whatever the schedule; a refusal is never repeated the same day; the 15-minute 5xx rule is met many times over; no human step (D-008's 3-day warning covers persistent refusals) | Membership can be up to ~a day old; a one-off refusal costs a day | Survives plan 4.1's extra runs unchanged; SupGP (4.2) can share the cooldown table and pick its own interval |
| Weekly | Least load | New launches (e.g. a Starlink batch) uncoloured for up to a week | – |
| After a refusal, stop until a human resets it (like the Space-Track login backoff) | Most cautious | Breaks "nothing needs a human more often than every 14 days"; runner-IP blocks we didn't cause would stop the feature | – |
| After a 5xx, retry next run; after 403/404/429/301, stop for 20 h | Closest to the policy's letter | Two rules to explain; the difference is hours | – |

## Decision (proposed)
- Download only when the landed copy is at least `CELESTRAK_MIN_HOURS` = 20 hours old.
- A refusal (any non-200 including 301, or a 200 that isn't the expected CSV) stops the download at once, is recorded
  in the ops DB (`audit.source_refusal`), and blocks every CelesTrak request for `CELESTRAK_REFUSAL_COOLDOWN_HOURS` =
  20 hours. The last good copy stays.
- 5 seconds between requests; 21 requests a day (the index page and 20 groups).
- Persistent refusal shows as the `celestrak` source's freshness warning after 72 hours (D-008's 3 days), emailed by
  D-037. The run never fails or holds a unit because of CelesTrak.

## Evidence
CelesTrak usage policy copy of 16 Nov 2026 (owner's archive, fetch run 45065085216). Tests in
`pipeline/ingestion/tests/test_celestrak_groups.py`: no request within 19.9 h of a 503, requests again after 20.1 h,
no download within 19 h of the last one, every refusal status (301, 403, 404, 429, 500, 503) stops at that request.

## Consequences
- A new constellation batch is coloured within a day of CelesTrak listing it.
- A manual re-run the same day never re-downloads.
- Changing either constant is a one-line config change.

## Revisit when
- Plan 4.1 adds runs and the owner wants fresher membership, or plan 4.2 needs a different SupGP interval.
- CelesTrak publishes limits for group downloads, or asks SatTrack to change.
- The 3-day freshness warning fires more than once a month.

## Related
D-008, D-026, D-037, D-040; roadmap 3.8, 4.1, 4.2.
