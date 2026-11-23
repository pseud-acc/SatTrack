# Decision records

One file per architecture decision, holding the full trade-off analysis behind the short entry in
[`../DECISIONS.md`](../DECISIONS.md). The log says *what* was decided; these files say *why*, what else was
considered, what evidence there was, and what would make it worth revisiting.

**Read these before scoping or building a feature.** Find the records whose component the feature touches, check
each one's "Revisit when" list, and raise any trigger that fires as a decision before building on top of it. This is
the context for every new feature's scope, for people and for Claude alike.

## Rules

- File name: `D-NNN-<short-slug>.md`, the same number as the log entry. One decision per file.
- Write the record in the PR that makes the decision, with the log entry.
- Accepted records aren't rewritten. When a decision changes, add a new record that supersedes it, mark the old one
  **Superseded by D-NNN** in both places, and link the two.
- Small corrections (a typo, a broken link, a revisit trigger that has fired) are fine.
- D-001 to D-012 were back-filled on 22 Nov 2026 from their PRs and log entries. Their option analyses are
  reconstructed from what those PRs recorded; anything not recorded at the time says so.

## Template

```markdown
# D-NNN Title

**Status:** Accepted | Proposed | Superseded by D-NNN · **Date:** YYYY-MM-DD · **PRs:** #NN
**Component:** where it applies · **Tier:** full (hard to reverse) | light (contained)

## Context
The problem and the constraints at the time.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|

## Decision
What was chosen, precisely enough to implement.

## Evidence
Measurements, tests, data checked. Say where and when.

## Consequences
What follows: new rules, checks, costs accepted.

## Revisit when
Concrete triggers (a number crossing a threshold, a planned feature arriving).

## Related
Other records and roadmap tasks.
```
