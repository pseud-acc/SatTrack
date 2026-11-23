"""CelesTrak constellation groups (D-026): download rules, keeping the last copy, and the dbt rules run on the result.

No network: a fake opener answers from the committed sample (tests/fixtures/celestrak/: a few real rows per group
from fetch run 45061938995, and a trimmed copy of the real GP index page from fetch run 45099334610). Download tests
that need a smaller index use a page built in the real page's markup. The dbt models are rendered by substituting source(), ref()
and the audit macro, then run in DuckDB on the landed tables, so the precedence, "Operational" and exclusion rules
and the new-group warning are tested in CI without a dbt build.
"""
from __future__ import annotations

import io
import re
import sys
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sattrack_ingest import audit, celestrak, celestrak_groups, config, raw_writer  # noqa: E402
from sattrack_ingest.config import RunContext  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "celestrak"
TRANSFORM = Path(__file__).resolve().parents[2] / "transform"
SAMPLE_GROUPS = ["starlink", "oneweb", "gps-ops", "glo-ops", "intelsat", "ses", "gnss"]
REAL_INDEX = FIXTURES / "gp_index_2026-11-23.html"     # trimmed copy of CelesTrak's GP index page, 23 Nov 2026
# The sample groups' titles as that page shows them.
TITLES = {"starlink": "Starlink", "oneweb": "OneWeb", "gps-ops": "GPS Operational", "glo-ops": "GLONASS Operational",
          "intelsat": "Intelsat", "ses": "SES", "gnss": "GNSS"}
HOUR = 3600.0


def index_html(groups=SAMPLE_GROUPS, titles=TITLES) -> str:
    """A smaller GP index page in the real page's markup: one cell per group (two per row), the title as text,
    then icon-only links to the CSV and the table."""
    cells = [f'<td align=center>{titles.get(g, g.title())} <a title="CSV Data" href="gp.php?GROUP={g}&FORMAT=csv">'
             f'<i class="fal fa-file-alt"></i></a> <a title="Table" href="table.php?GROUP={g}&FORMAT=csv">'
             f'<i class="fal fa-table"></i></a></td>' for g in groups]
    rows = "".join(f"<tr>{''.join(cells[i:i + 2])}</tr>" for i in range(0, len(cells), 2))
    return ('<table class="center outline"><tr><td><table class=striped><thead><tr class=header>'
            f'<th colspan=2>Communications Satellites</th></tr></thead><tbody>{rows}</tbody></table></td></tr></table>')


def sample(group: str) -> str:
    return (FIXTURES / f"{group}.csv").read_text(encoding="utf-8")


class Fake:
    """Answers URLs from a dict; an int is an HTTP error status. Records every request."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def __call__(self, request, timeout):
        url = request.full_url
        self.calls.append(url)
        answer = self.answers[url]
        if isinstance(answer, int):
            raise urllib.error.HTTPError(url, answer, "refused", {}, None)
        return io.BytesIO(answer.encode())


def answers(groups=SAMPLE_GROUPS, **override) -> dict:
    out = {celestrak.INDEX_URL: index_html(groups)}
    out.update({celestrak.GROUP_URL.format(group=g): sample(g) for g in groups if (FIXTURES / f"{g}.csv").exists()})
    out.update({celestrak.GROUP_URL.format(group=g): v for g, v in override.items()})
    return out


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(raw_writer, "RAW_HISTORY_DIR", tmp_path / "raw_history")
    con = duckdb.connect(str(tmp_path / "wh.duckdb"))
    ops = duckdb.connect(str(tmp_path / "ops.duckdb"))
    ops.execute(audit.DDL)
    yield con, ops
    con.close()
    ops.close()


def ingest(env, fake, clock=None, run="run_2026-11-23T031700Z"):
    con, ops = env
    clock = clock or Clock(time.time())
    ctx = RunContext(run_id=run, loaded_at=datetime.fromtimestamp(clock(), timezone.utc).isoformat())
    pauses = []
    out = celestrak_groups.ingest_celestrak_groups(con, ops, ctx, opener=fake, sleep=pauses.append, clock=clock)
    return out, pauses


def members(con):
    return con.execute('select "GROUP", "NORAD_CAT_ID" from raw_celestrak.gp_group_member order by 1, 2').fetchall()


# ---------------------------------------------------------------- the group config


def test_config_lists_d026_groups_in_order_and_covers_the_whole_index():
    assert [g for g, _ in celestrak_groups.included_groups()] == [
        "starlink", "oneweb", "kuiper", "qianfan", "hulianwang", "iridium-NEXT", "globalstar", "orbcomm", "gps-ops",
        "glo-ops", "galileo", "beidou", "tdrss", "dmc", "planet", "spire", "intelsat", "ses", "eutelsat", "telesat"]
    included = {g for g, _ in celestrak_groups.included_groups()}
    assert not included & set(config.CELESTRAK_EXCLUDED_GROUPS)
    assert len(included) + len(config.CELESTRAK_EXCLUDED_GROUPS) == 47   # the 47 groups the index showed on 22 Nov


def test_new_group_on_the_index_is_reported():
    assert celestrak_groups.not_in_config(["starlink", "gnss", "new-mega-constellation"]) == ["new-mega-constellation"]


# ---------------------------------------------------------------- the index page


def test_titles_come_from_each_groups_row_not_from_format_links():
    assert celestrak.group_titles(index_html()) == TITLES


def test_the_real_index_page_lists_47_groups_all_known_and_titled():
    """The page as CelesTrak served it on 23 Nov 2026 (fetch run 45099334610): two groups per row in places,
    group tables nested in a layout table, titles as plain text before icon-only links."""
    html = REAL_INDEX.read_text(encoding="utf-8")
    listed = celestrak.groups_on_index(html)
    titles = celestrak.group_titles(html)
    assert len(listed) == 47 and set(titles) == set(listed)
    assert celestrak_groups.not_in_config(listed) == []
    assert {g: titles[g] for g, _ in celestrak_groups.included_groups()} == {
        "starlink": "Starlink", "oneweb": "OneWeb", "kuiper": "Kuiper", "qianfan": "Qianfan",
        "hulianwang": "Hulianwang Digui", "iridium-NEXT": "Iridium NEXT", "globalstar": "Globalstar",
        "orbcomm": "Orbcomm", "gps-ops": "GPS Operational", "glo-ops": "GLONASS Operational", "galileo": "Galileo",
        "beidou": "Beidou", "tdrss": "Tracking and Data Relay Satellite System (TDRSS)", "dmc": "Disaster Monitoring",
        "planet": "Planet", "spire": "Spire", "intelsat": "Intelsat", "ses": "SES", "eutelsat": "Eutelsat",
        "telesat": "Telesat"}
    assert titles["active"] == "Active Satellites" and titles["sarsat"] == "Search & Rescue (SARSAT)"
    assert [r["GROUP"] for r in celestrak_groups.parse_index(html)][:2] == ["last-30-days", "stations"]


def test_titles_from_plain_links_outside_a_table():
    html = '<a href="gp.php?GROUP=gps-ops&FORMAT=tle">GPS Operational</a> <a href="gp.php?GROUP=ses&FORMAT=tle">SES</a>'
    assert celestrak.group_titles(html) == {"gps-ops": "GPS Operational", "ses": "SES"}


def test_two_groups_in_one_row_each_keep_their_own_title():
    html = ('<table><tr><td>GPS Operational <a href="gp.php?GROUP=gps-ops&FORMAT=csv"><i></i></a></td>'
            '<td>GLONASS Operational <a href="gp.php?GROUP=glo-ops&FORMAT=csv"><i></i></a></td></tr></table>')
    assert celestrak.group_titles(html) == {"gps-ops": "GPS Operational", "glo-ops": "GLONASS Operational"}


def test_an_index_without_titles_for_configured_groups_is_a_layout_change():
    html = '<a href="gp.php?GROUP=starlink&FORMAT=tle">TLE</a>'
    with pytest.raises(celestrak_groups.LayoutChanged, match="no title"):
        celestrak_groups.parse_index(html)
    with pytest.raises(celestrak_groups.LayoutChanged, match="no groups"):
        celestrak_groups.parse_index("<html>maintenance</html>")


# ---------------------------------------------------------------- downloading


def test_downloads_only_included_groups_in_order_with_a_pause(env):
    fake = Fake(answers())
    out, pauses = ingest(env, fake)
    assert out["stage_status"] == "ok"
    # gnss is excluded: never requested; included groups not on this index (kuiper, ...) are never requested either
    assert fake.calls == [celestrak.INDEX_URL] + [celestrak.GROUP_URL.format(group=g) for g in
                                                   ["starlink", "oneweb", "gps-ops", "glo-ops", "intelsat", "ses"]]
    assert all(u.endswith("&FORMAT=csv") for u in fake.calls[1:])
    assert pauses == [config.CELESTRAK_PAUSE_S] * 6
    con, ops = env
    assert out["gp_group_member"] == 18 and len(members(con)) == 18
    assert ("starlink", "44714") in members(con) and not [m for m in members(con) if m[0] == "gnss"]
    assert out["gp_group_index"] == 7


def test_requests_gzip_and_never_follow_redirects():
    seen = {}

    def opener(request, timeout):
        seen["ae"] = request.get_header("Accept-encoding")
        raise urllib.error.HTTPError(request.full_url, 301, "moved", {}, None)
    with pytest.raises(celestrak.Refused) as e:
        celestrak.get(celestrak.INDEX_URL, opener)
    assert seen["ae"] == "gzip" and e.value.status == 301
    assert any(isinstance(h, celestrak._NoRedirect) for h in celestrak._OPENER.handlers)


@pytest.mark.parametrize("status", [301, 403, 404, 429, 500, 503])
def test_a_refusal_stops_at_once_and_keeps_the_last_copy(env, status):
    con, ops = env
    clock = Clock(1_800_000_000.0)
    ingest(env, Fake(answers()), clock)
    before = members(con)
    clock.t += 24 * HOUR
    fake = Fake(answers(oneweb=status))
    out, _ = ingest(env, fake, clock, run="run_2026-11-24T031700Z")
    assert out["stage_status"] == "skipped" and f"HTTP {status}" in out["reason"] and "kept last copy" in out["reason"]
    # stopped at the refused request: no later group, no retry
    assert fake.calls == [celestrak.INDEX_URL, celestrak.GROUP_URL.format(group="starlink"),
                          celestrak.GROUP_URL.format(group="oneweb")]
    assert members(con) == before                      # all or nothing: starlink was not replaced on its own
    assert ops.execute("select http_status from audit.source_refusal").fetchall() == [(status,)]


def test_a_refused_index_requests_nothing_else(env):
    fake = Fake({celestrak.INDEX_URL: 403})
    out, pauses = ingest(env, fake)
    assert fake.calls == [celestrak.INDEX_URL] and pauses == []
    assert out["stage_status"] == "skipped"


def test_no_requests_during_the_cooldown_after_a_refusal(env):
    clock = Clock(1_800_000_000.0)
    ingest(env, Fake({celestrak.INDEX_URL: 503}), clock)
    for hours in (0.25, 1, 19.9):           # covers the policy's 15 minutes after a 5xx, and the next runs that day
        clock.t = 1_800_000_000.0 + hours * HOUR
        fake = Fake(answers())
        out, _ = ingest(env, fake, clock)
        assert fake.calls == [] and "refused" in out["reason"]
    clock.t = 1_800_000_000.0 + 20.1 * HOUR
    fake = Fake(answers())
    out, _ = ingest(env, fake, clock)
    assert out["stage_status"] == "ok" and fake.calls


def test_at_most_once_per_min_hours(env):
    clock = Clock(1_800_000_000.0)
    ingest(env, Fake(answers()), clock)
    clock.t += 19 * HOUR
    fake = Fake(answers())
    out, _ = ingest(env, fake, clock)
    assert fake.calls == [] and out["stage_status"] == "skipped" and "landed 19.0 h ago" in out["reason"]


@pytest.mark.parametrize("body", ["GP data has not updated since your last download", "<html>busy</html>",
                                  "OBJECT_NAME,OBJECT_ID\nX,2000-001A\n"])
def test_a_body_that_is_not_the_expected_csv_keeps_the_last_copy(env, body):
    con, _ = env
    clock = Clock(1_800_000_000.0)
    ingest(env, Fake(answers()), clock)
    before = members(con)
    clock.t += 24 * HOUR
    out, _ = ingest(env, Fake(answers(starlink=body)), clock)
    assert out["stage_status"] == "skipped" and members(con) == before


def test_a_layout_change_keeps_the_last_copy_without_a_refusal(env):
    con, ops = env
    clock = Clock(1_800_000_000.0)
    ingest(env, Fake(answers()), clock)
    before = members(con)
    clock.t += 24 * HOUR
    out, _ = ingest(env, Fake({celestrak.INDEX_URL: "<html>new design</html>"}), clock)
    assert "layout changed" in out["reason"] and members(con) == before
    assert ops.execute("select count(*) from audit.source_refusal").fetchone()[0] == 0


def test_a_first_run_that_gets_nothing_leaves_empty_tables_for_dbt(env):
    con, _ = env
    out, _ = ingest(env, Fake({celestrak.INDEX_URL: 403}))
    assert out["created_empty"] == ["gp_group_member", "gp_group_index"]
    assert members(con) == []
    assert con.execute("select count(*) from raw_celestrak.group_config").fetchone()[0] == 47


def test_reports_index_groups_not_in_config(env):
    out, _ = ingest(env, Fake(answers(SAMPLE_GROUPS + ["new-mega-constellation"])))
    assert out["groups_not_in_config"] == ["new-mega-constellation"]


# ---------------------------------------------------------------- the dbt models on the landed sample


def render(sql: str) -> str:
    sql = re.sub(r"\{\{\s*config\([^)]*\)\s*\}\}", "", sql)
    sql = re.sub(r"\{\{\s*source\('celestrak',\s*'(\w+)'\)\s*\}\}", r"raw_celestrak.\1", sql)
    sql = re.sub(r"\{\{\s*ref\('(\w+)'\)\s*\}\}", r"\1", sql)
    return sql.replace("{{ helper__audit_fields() }}",
                       "cast(current_timestamp as timestamp) as inserted_date_time, 'test' as inserted_by")


def build_models(con):
    for name in ("stg__celestrak__gp_group_member", "stg__celestrak__gp_group_index", "stg__celestrak__group_config"):
        con.execute(f"create or replace view {name} as "
                    + render((TRANSFORM / "models" / "staging" / "celestrak" / f"{name}.sql").read_text(encoding="utf-8")))
    sql = (TRANSFORM / "models" / "intermediate" / "satellite" / "int__celestrak__satellite_constellation.sql")
    con.execute("create or replace view int__celestrak__satellite_constellation as "
                + render(sql.read_text(encoding="utf-8")))


def constellations(con):
    return dict(con.execute("select satcat_id, constellation from int__celestrak__satellite_constellation").fetchall())


def test_models_name_each_object_once_by_the_d026_rules(env):
    con, _ = env
    # made-up overlaps to exercise precedence: a GPS satellite also in ses, an Intelsat satellite also in ses
    ses = sample("ses") + sample("gps-ops").splitlines()[1] + "\n" + sample("intelsat").splitlines()[1] + "\n"
    ingest(env, Fake(answers(ses=ses)))
    build_models(con)
    got = constellations(con)
    assert got[44714] == "Starlink"            # STARLINK-1008
    assert got[26407] == "GPS"                 # GPS BIIR-5: gps-ops beats ses (constellations first); "Operational" gone
    assert got[32275] == "GLONASS"             # COSMOS 2433
    assert got[26900] == "Intelsat"            # INTELSAT 902: intelsat beats ses (earlier operator)
    assert got[26554] == "SES"                 # NSS-11
    assert len(got) == 18                      # 3 rows x 6 included groups; gnss (excluded) adds nobody
    assert con.execute("select count(*) from int__celestrak__satellite_constellation "
                       "group by satcat_id having count(*) > 1").fetchall() == []


def test_models_on_the_real_index_page(env):
    """The whole flow on the real page: every included group requested once in config order, display names from
    CelesTrak's titles. Groups without committed rows answer with the CSV header only."""
    con, _ = env
    header = sample("starlink").splitlines()[0] + "\n"
    answer = {celestrak.INDEX_URL: REAL_INDEX.read_text(encoding="utf-8")}
    answer.update({celestrak.GROUP_URL.format(group=g): (sample(g) if (FIXTURES / f"{g}.csv").exists() else header)
                   for g, _ in celestrak_groups.included_groups()})
    fake = Fake(answer)
    out, _ = ingest(env, fake)
    assert out["stage_status"] == "ok" and "groups_not_in_config" not in out
    assert fake.calls[1:] == [celestrak.GROUP_URL.format(group=g) for g, _ in celestrak_groups.included_groups()]
    build_models(con)
    got = constellations(con)
    assert (got[44714], got[26407], got[32275], got[44057]) == ("Starlink", "GPS", "GLONASS", "OneWeb")
    test_sql = TRANSFORM / "tests" / "singular" / "assert__stg__celestrak__gp_group_index__groups_in_config.sql"
    assert con.execute(render(test_sql.read_text(encoding="utf-8"))).fetchall() == []   # config matches the page


def test_new_group_check_warns_on_unknown_and_vanished_groups(env):
    con, _ = env
    ingest(env, Fake(answers(SAMPLE_GROUPS + ["new-mega-constellation"])))
    build_models(con)
    test_sql = TRANSFORM / "tests" / "singular" / "assert__stg__celestrak__gp_group_index__groups_in_config.sql"
    text = test_sql.read_text(encoding="utf-8")
    assert re.search(r"config\(severity='warn'\)", text)       # warns, never fails the build
    rows = set(con.execute(render(text)).fetchall())
    assert ("not_in_config", "new-mega-constellation") in rows
    # included groups this (sample) index doesn't list are reported too, e.g. kuiper
    assert ("included_not_on_index", "kuiper") in rows
    assert not [r for r in rows if r[1] in SAMPLE_GROUPS]


def test_new_group_check_is_quiet_before_any_download(env):
    con, _ = env
    ingest(env, Fake({celestrak.INDEX_URL: 403}))
    build_models(con)
    text = (TRANSFORM / "tests" / "singular" / "assert__stg__celestrak__gp_group_index__groups_in_config.sql")
    assert con.execute(render(text.read_text(encoding="utf-8"))).fetchall() == []
    assert constellations(con) == {}
