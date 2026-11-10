# Tests for the bespoke dbt-bouncer checks

Unit tests for every `check_bespoke_*` check in `bouncer/bespoke/manifest/`. Each check has at least one
passing and one failing case; the sqlglot-based checks also cover Jinja placeholders (`ref`, `source`,
macro calls, `{% %}` blocks, `{# #}` comments, in-file `{{ config() }}`), CTE naming, leading commas,
subqueries in FROM/JOIN, unused CTEs, mart join/default/cast rules and explicit final casts.

The tests use dbt-bouncer's own harness (`dbt_bouncer.testing.check_passes` / `check_fails`), which builds
resources as the runner does (`DictProxy` nodes, a `CheckContext`) and loads the checks from
`bouncer/bespoke` as `custom_checks_dir` does. No manifest, dbt or warehouse is needed.
`test_coverage.py` fails if a bespoke check is defined or configured in `dbt-bouncer.yml` without tests.

## Run

From `transform/`, with the bouncer venv (it has dbt-bouncer and pytest; see `bouncer/requirements.txt`):

```
<bouncer venv>/Scripts/python.exe -m pytest bouncer/tests -q -p no:cacheprovider
```

`-p no:cacheprovider` keeps pytest from writing a `.pytest_cache` folder into the project.
