"""Which pull-request checks a change needs (pr.yml's `changes` job).

Reads the PR's changed file paths (one per line) on stdin and writes app_build, app_tests, app_e2e and pipeline
(true/false) to $GITHUB_OUTPUT, plus a table to $GITHUB_STEP_SUMMARY. pr.yml passes each value to its reusable
workflow's `run` input; a workflow told not to run skips its job, and GitHub counts a skipped job as passing for the
`protect-main` required checks, so a docs-only PR merges without building the app.

Conservative by design: a path no rule recognises runs everything, and so does a change to this gate itself
(pr.yml, this script) or any reusable check workflow's own dependencies. merge.yml always runs every check before a
deploy, whatever this script says.

    python .github/scripts/pr_changes.py < files.txt
    python .github/scripts/pr_changes.py --all      # the fallback: run everything (e.g. the file list failed)
"""
import os
import sys
from fnmatch import fnmatch

CHECKS = ("app_build", "app_tests", "app_e2e", "pipeline")

# Paths that need no check at all: documentation and repo metadata that nothing builds or tests.
DOCS = ("*.md", "docs/*", "LICENSE", ".gitignore", ".github/ISSUE_TEMPLATE/*", ".github/dependabot.yml",
        ".claude/*")

# Changing the gate (or the workflows it feeds) runs everything.
GATE = (".github/workflows/pr.yml", ".github/scripts/pr_changes.py")

# Paths outside the app's slug (merge.yml's "reaches the app" rule: pipeline/, infra/, tests/ are in .slugignore,
# plus .github/ and documentation). Anything else is the app: run the app checks.
NOT_APP = ("pipeline/*", "infra/*", "tests/*", ".github/*")

RULES = {   # check -> extra paths (beyond app files) that need it
    "app_build": ("tests/app_data/*", ".github/workflows/app-build.yml", ".github/scripts/heroku_build_check.sh"),
    "app_tests": ("tests/app/*", "tests/app_data/*", "tests/contracts/*", "tests/conftest.py",
                  ".github/workflows/app-tests.yml"),
    "app_e2e": ("tests/e2e/*", "tests/app/*", "tests/app_data/*", "tests/contracts/*", "tests/conftest.py",
                ".github/workflows/app-e2e.yml"),
    "pipeline": ("pipeline/*", "infra/*", "app/contracts/*", "tests/contracts/*", ".github/scripts/pipeline_report.py",
                 ".github/workflows/pipeline-checks.yml"),
}


def matches(path, patterns):
    return any(fnmatch(path, p) for p in patterns)


def decide(paths):
    """{check: bool} for the changed paths, and {path: reason} for the summary."""
    need = dict.fromkeys(CHECKS, False)
    why = {}
    for path in (p.strip() for p in paths):
        if not path:
            continue
        if matches(path, GATE):
            need = dict.fromkeys(CHECKS, True)
            why[path] = "the PR gate itself: every check"
            continue
        # Markdown under pipeline/ is not just documentation: dbt doc blocks and the column definitions feed dbt
        # parse and the docs registry check.
        if matches(path, DOCS) and not path.startswith("pipeline/"):
            why[path] = "documentation: no check"
            continue
        hits = [c for c, pats in RULES.items() if matches(path, pats)]
        if not matches(path, NOT_APP):
            hits = sorted(set(hits) | {"app_build", "app_tests", "app_e2e"})
        if not hits:   # under tests/, pipeline/ ... but no rule knows it, or a new .github file: be safe
            hits = list(CHECKS)
            why[path] = "not recognised: every check"
        else:
            why[path] = ", ".join(hits)
        for c in hits:
            need[c] = True
    return need, why


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--all" in argv:
        need, why = dict.fromkeys(CHECKS, True), {"(file list unavailable)": "every check"}
    else:
        paths = sys.stdin.read().splitlines()
        if not [p for p in paths if p.strip()]:
            need, why = dict.fromkeys(CHECKS, True), {"(no files listed)": "every check"}
        else:
            need, why = decide(paths)
    out = os.environ.get("GITHUB_OUTPUT")
    lines = [f"{c}={'true' if need[c] else 'false'}" for c in CHECKS]
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### Checks this PR needs\n\n| Check | Runs |\n|---|---|\n")
            f.write("".join(f"| {c} | {'yes' if need[c] else 'skipped'} |\n" for c in CHECKS))
            f.write("\n<details><summary>Why, per file</summary>\n\n| File | Needs |\n|---|---|\n")
            f.write("".join(f"| `{p}` | {r} |\n" for p, r in list(why.items())[:200]))
            f.write("\n</details>\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
