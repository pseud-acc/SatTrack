# D-037 Pipeline warnings email a summary without failing the run

**Status:** Accepted · **Date:** 2026-11-23 · **PRs:** this PR (`fix/pipeline-warnings-notify`)
**Component:** `.github/scripts/pipeline_report.py`, `.github/workflows/pipeline.yml` (`notify` job),
`pipeline/run_pipeline.py` (warning streaks) · **Tier:** light (contained; easy to change back)

## Context
Since #43 the run report failed the job on any result other than OK, so GitHub would email the owner. Result WARN
covered two different things: a unit that didn't publish (a real problem, as on 18 Nov when GCAT details were held)
and a run where every unit published but a stage warned (source freshness). Run 45091163953 on 23 Nov published all
its data, including the first `objects.json`, yet showed a red failure. The owner called that a misleading alert:
warnings should email a summary but not fail. Warn-severity dbt checks didn't alert at all, because they leave the
result OK. The owner also asked to see how long each warning has been going on.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Open or comment on one "Pipeline warnings" issue from a separate job with only `issues: write`** | GitHub emails watchers on new issues and comments; no new account and no AWS change; one place shows the history; closed automatically by the next run without warnings | The summary is public (it already is, in the Actions log); depends on the owner watching the repo (checked: subscribed) | Several runs a day (4.1) still post into one thread |
| Email through AWS SES | A real email from the pipeline | New AWS resources and IAM permissions, a verified sender, SES sandbox limits; more to maintain | – |
| A warning annotation only, no email | Least noise | Warnings go unseen unless someone opens the run | – |

Frequency: the owner chose **an email on every run with warnings**, over emailing only when the set of warnings
changes. A permanent warning would then email daily, so the one such check found (`fk__dim__org__org_parent_code`,
2 rows) is logged to fix in #65.

## Decision
- **Problem** (job fails, GitHub emails): non-zero exit, a unit not published (held or error), no run summary, failed
  commit to S3, no app export, stale positions (> 30 h) or details (> 14 days). Unchanged except that WARN with every
  unit published is no longer a problem.
- **Warning** (job passes, with a `::warning` annotation): a dbt check at warn severity, or a source past its
  freshness limit, in a run with no problem.
- The report writes `status` (problem / warning / ok / skipped) and the Markdown summary to its step outputs. The
  `notify` job (no AWS access, `issues: write` only, not on dry runs) comments the summary on the open issue labelled
  `pipeline-warnings`, or opens one; a run with status ok closes it.
- **How long:** each warning shows when its current unbroken run of warnings began and how many runs that covers,
  e.g. `warning for 2.1 days (3 runs, since 2026-11-21 03:18 UTC)`. Checks use Elementary's per-run results
  (`elementary.elementary_test_results`); sources use `audit.source_freshness`. Both live in the ops DB, which the
  state script carries between runs. A pass or a failure ends a streak.

## Evidence
Run 45091163953 (23 Nov 00:51 UTC): exit 0, `tracking=ok enrichment=ok`, promoted, result WARN from
`source_freshness=warn`; the checks `fk__dim__org__org_parent_code` and `mh__stg__jsr__launchlog__pk_unique` warned
(2 rows each). Tests: `pipeline/ingestion/tests/test_pipeline_report.py` (this run's shape is a warning, not a
failure; the 18 Nov held run is still a problem), `test_audit_flags.py` (streaks), `test_runlog.py` (the run log's
"since" text matches what the report parses).

## Consequences
- The issue is public, so its body is exactly the public report: check and source names, row counts of failing
  checks, dates. Never row data or object identifiers (tested).
- A warning that never clears emails every run: fix its cause or change its severity with a decision, never
  ignore it. #65 tracks the one known today.
- History starts from what the ops DB holds; streaks older than the ops DB show from its first run.

## Revisit when
- Several runs a day (plan 4.1) make an email per run too frequent: switch to emailing only when the set of
  warnings changes (the alternative the owner considered).
- The owner stops watching the repo or changes notification settings: the email path depends on it.
- A warning turns out to need action every time: promote that check to error severity instead.

## Related
D-001 (the gate), D-002 (repeated GCAT JCAT is a warning below 10), #43 (the original alert), #65.
