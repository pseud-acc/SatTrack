"""CelesTrak groups (D-026, D-047): download rules, keeping the last copy, and the dbt rules run on the result.

No network: a fake opener answers from the committed sample (tests/fixtures/celestrak/: a few real rows per group
from fetch run 45061938995, and a trimmed copy of the real GP index page from fetch run 45099334610). Download tests
that need a smaller index use a page built in the real page's markup. The dbt models are rendered by substituting source(), ref()
and the audit macro, then run in DuckDB on the landed tables, so the display names, the name-fit flag (D-046, D-047),
the kinds and the new-group warning are tested in CI without a dbt build.
"""
from __future__ import annotations

import csv
import io
import re
import sys
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import jinja2
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


def test_config_lists_d047_groups_in_order_and_covers_the_whole_index():
    assert celestrak_groups.included_groups() == (
        [(g, "constellation") for g in ("starlink", "oneweb", "kuiper", "qianfan", "hulianwang", "iridium-NEXT",
                                         "globalstar", "orbcomm")]
        + [(g, "system") for g in ("gps-ops", "glo-ops", "galileo", "beidou", "tdrss", "dmc")]
        + [("sarsat", "system_hosted"), ("sbas", "system_hosted_umbrella"), ("stations", "station")])
    # D-047: gnss is the umbrella term for all navigation systems, not a system; it isn't downloaded
    assert "gnss" in config.CELESTRAK_EXCLUDED_GROUPS
    # D-047: operator fleets are neither constellations nor systems, so they are no longer downloaded
    assert {"planet", "spire", "intelsat", "ses", "eutelsat", "telesat"} <= set(config.CELESTRAK_EXCLUDED_GROUPS)
    included = {g for g, _ in celestrak_groups.included_groups()}
    assert not included & set(config.CELESTRAK_EXCLUDED_GROUPS)
    assert len(included) + len(config.CELESTRAK_EXCLUDED_GROUPS) == 47   # the 47 groups the index showed on 22 Nov


def test_member_name_prefixes_are_landed_with_the_config(monkeypatch):
    # D-046 mechanism kept; no group needs a prefix since D-047 (tdrss's members must fit its most common word, TDRS)
    assert config.CELESTRAK_MEMBER_NAME_PREFIX == {}
    records = celestrak_groups.config_records()
    assert all(r["GROUP_MEMBER_NAME_PREFIX"] == "" for r in records)
    monkeypatch.setattr(celestrak_groups, "CELESTRAK_MEMBER_NAME_PREFIX", {"tdrss": "TDRS"})
    records = celestrak_groups.config_records()
    assert {r["GROUP"]: r["GROUP_MEMBER_NAME_PREFIX"] for r in records if r["GROUP_MEMBER_NAME_PREFIX"]} == {"tdrss": "TDRS"}


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
        "sarsat": "Search & Rescue (SARSAT)",
        "sbas": "Satellite-Based Augmentation System (WAAS/EGNOS/MSAS)", "stations": "Space Stations"}
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
    # gnss, intelsat and ses are excluded (D-047): never requested; included groups not on this index (kuiper, ...)
    # are never requested either
    assert fake.calls == [celestrak.INDEX_URL] + [celestrak.GROUP_URL.format(group=g) for g in
                                                   ["starlink", "oneweb", "gps-ops", "glo-ops"]]
    assert all(u.endswith("&FORMAT=csv") for u in fake.calls[1:])
    assert pauses == [config.CELESTRAK_PAUSE_S] * 4
    con, ops = env
    assert out["gp_group_member"] == 12 and len(members(con)) == 12
    assert ("starlink", "44714") in members(con) and not [m for m in members(con) if m[0] in ("gnss", "intelsat", "ses")]
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


CELESTRAK_MACROS = TRANSFORM / "macros" / "celestrak"


def render(sql: str) -> str:
    """source(), ref(), config() and the audit macro by substitution; the CelesTrak helper macros (D-046) by Jinja,
    from their committed files, so the tests run the same exception logic as dbt."""
    sql = re.sub(r"\{\{\s*config\([^)]*\)\s*\}\}", "", sql)
    sql = re.sub(r"\{\{\s*source\('celestrak',\s*'(\w+)'\)\s*\}\}", r"raw_celestrak.\1", sql)
    sql = re.sub(r"\{\{\s*ref\('(\w+)'\)\s*\}\}", r"\1", sql)
    sql = sql.replace("{{ helper__audit_fields() }}",
                      "cast(current_timestamp as timestamp) as inserted_date_time, 'test' as inserted_by")
    macros = "".join(p.read_text(encoding="utf-8") for p in sorted(CELESTRAK_MACROS.glob("helper__*.sql")))
    return jinja2.Environment().from_string(macros + sql).render()


GROUP_MEMBERSHIP = TRANSFORM / "models" / "intermediate" / "satellite" / "int__celestrak__satellite_group_membership.sql"


def build_models(con):
    for name in ("stg__celestrak__gp_group_member", "stg__celestrak__gp_group_index", "stg__celestrak__group_config"):
        con.execute(f"create or replace view {name} as "
                    + render((TRANSFORM / "models" / "staging" / "celestrak" / f"{name}.sql").read_text(encoding="utf-8")))
    con.execute("create or replace view int__celestrak__satellite_group_membership as "
                + render(GROUP_MEMBERSHIP.read_text(encoding="utf-8")))


def memberships(con) -> dict:
    """{(satcat_id, group): (kind, display name, flag_name_fits_group)}"""
    rows = con.execute("select satcat_id, celestrak_group, celestrak_group_kind, grouping_name, flag_name_fits_group "
                       "from int__celestrak__satellite_group_membership").fetchall()
    return {(r[0], r[1]): r[2:] for r in rows}


def constellations(con) -> dict:
    """{satcat_id: name} of constellation group memberships (first in config order), as int__xsrc__ takes them."""
    rows = con.execute("select satcat_id, arg_min(grouping_name, celestrak_group_order) "
                       "from int__celestrak__satellite_group_membership where celestrak_group_kind = 'constellation' "
                       "group by satcat_id").fetchall()
    return dict(rows)


def test_group_membership_names_kinds_and_exclusions(env):
    con, _ = env
    ingest(env, Fake(answers()))
    build_models(con)
    got = memberships(con)
    assert got[(44714, "starlink")] == ("constellation", "Starlink", 1)     # STARLINK-1008
    assert got[(26407, "gps-ops")] == ("system", "GPS", 1)                  # GPS BIIR-5: "Operational" gone
    assert got[(32275, "glo-ops")] == ("system", "GLONASS", 1)              # COSMOS 2433
    # D-047: intelsat and ses are operator fleets and gnss an umbrella term: excluded, never downloaded or counted
    assert not [k for k in got if k[1] in ("intelsat", "ses", "gnss")]
    assert len(got) == 12                      # 3 rows x 4 downloaded groups of the sample (starlink, oneweb, gps-ops,
    #                                            glo-ops)


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
    got = memberships(con)
    assert (got[(44714, "starlink")][1], got[(26407, "gps-ops")][1], got[(32275, "glo-ops")][1],
            got[(44057, "oneweb")][1]) == ("Starlink", "GPS", "GLONASS", "OneWeb")
    # D-047: tdrss is a system group; its relay satellites fit (most common leading word TDRS), the spacecraft
    # CelesTrak lists there as TDRSS users don't, so the system model drops them
    assert got[(19548, "tdrss")] == ("system", "Tracking and Data Relay Satellite System (TDRSS)", 1)   # TDRS 3
    assert got[(20580, "tdrss")][2] == 0 and got[(25544, "tdrss")][2] == 0                              # HST, ISS
    test_sql = TRANSFORM / "tests" / "singular" / "assert__stg__celestrak__gp_group_index__groups_in_config.sql"
    assert con.execute(render(test_sql.read_text(encoding="utf-8"))).fetchall() == []   # config matches the page
    assert con.execute(render(NAME_CHECK.read_text(encoding="utf-8"))).fetchall() == []  # every name fits its group


NAME_CHECK = TRANSFORM / "tests" / "singular" / "assert__int__celestrak__satellite_group_membership__names_fit_group.sql"


def test_name_check_warns_on_a_member_whose_name_does_not_fit(env):
    """D-046: a constellation member whose name lacks its group's usual leading word (or the group's prefix) is
    reported; system groups drop such members by rule (D-047) and aren't reported. HST in starlink is made up for the
    test; HST in tdrss is real (a TDRSS user)."""
    con, _ = env
    hst = sample("tdrss").splitlines()[2] + "\n"                    # HST,1990-037B,...,20580,...
    ingest(env, Fake(answers(SAMPLE_GROUPS + ["tdrss"], starlink=sample("starlink") + hst)))
    build_models(con)
    text = NAME_CHECK.read_text(encoding="utf-8")
    assert re.search(r"config\(severity='warn'\)", text)       # warns, never fails the build
    rows = con.execute(render(text)).fetchall()
    assert rows == [("name_lacks_expected_string", "starlink", 20580, "HST", "STARLINK")]


def group_csv(rows: list[tuple[str, str, int]]) -> str:
    """A group CSV in CelesTrak's columns: (OBJECT_NAME, OBJECT_ID, NORAD_CAT_ID) per row, the elements of the
    starlink sample's first row (only the three identifying columns matter to the models)."""
    header, first = list(csv.reader(io.StringIO(sample("starlink"))))[:2]
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(header)
    for name, object_id, norad in rows:
        row = dict(zip(header, first), OBJECT_NAME=name, OBJECT_ID=object_id, NORAD_CAT_ID=str(norad))
        w.writerow([row[c] for c in header])
    return out.getvalue()


def test_name_check_exceptions_live_in_the_macro(env):
    """Names and NORAD ids from fetch run 45061938995. D-047 removed D-046's dmc exception: dmc's most common leading
    word is DMC (DMC3-FM1..3), so BEIJING 1, HJ-1A and YAOGAN-4 don't fit (UK-DMC 2 does); GCAT adds BEIJING 1 and
    DEIMOS-1 back through the DMC programme in the system model. hulianwang still accepts GUOWANG. HST in hulianwang
    is made up: an unrelated name in a constellation group still warns."""
    con, _ = env
    dmc = group_csv([("BEIJING 1", "2005-043A", 28890), ("HUANJING 1A (HJ-1A)", "2008-041A", 33320),
                     ("YAOGAN-4", "2008-061A", 33446), ("DEIMOS-1", "2009-041A", 35681),
                     ("UK-DMC 2", "2009-041C", 35683), ("DMC3-FM1", "2015-032A", 40715),
                     ("DMC3-FM2", "2015-032B", 40716), ("DMC3-FM3", "2015-032C", 40717)])
    hulianwang = group_csv([("HULIANWANG DIGUI-01", "2024-240A", 62323), ("HULIANWANG DIGUI-02", "2024-240B", 62324),
                            ("GUOWANG-30 OBJECT A", "2026-260A", 101416), ("HST", "1990-037B", 20580)])
    ingest(env, Fake(answers(SAMPLE_GROUPS + ["dmc", "hulianwang"], dmc=dmc, hulianwang=hulianwang)))
    build_models(con)
    got = memberships(con)
    assert [got[(n, "dmc")][2] for n in (28890, 33320, 33446, 35681, 35683, 40715)] == [0, 0, 0, 0, 1, 1]
    assert got[(101416, "hulianwang")][1:] == ("Hulianwang", 1)
    rows = con.execute(render(NAME_CHECK.read_text(encoding="utf-8"))).fetchall()
    assert rows == [("name_lacks_expected_string", "hulianwang", 20580, "HST", "HULIANWANG")]
    macro = (CELESTRAK_MACROS / "helper__flag_member_name_fits_group.sql").read_text(encoding="utf-8")
    assert "{{ helper__flag_member_name_fits_group(" in GROUP_MEMBERSHIP.read_text(encoding="utf-8")
    assert "= 'dmc'" not in macro and "'GUOWANG'" in macro


def test_name_check_warns_when_a_prefix_matches_no_member(env, monkeypatch):
    con, _ = env
    monkeypatch.setattr(celestrak_groups, "CELESTRAK_MEMBER_NAME_PREFIX", {"tdrss": "TDRS"})   # none set since D-047
    renamed = sample("tdrss").replace("TDRS ", "RELAY ")         # made up: CelesTrak renames the relay satellites
    ingest(env, Fake(answers(SAMPLE_GROUPS + ["tdrss"], tdrss=renamed)))
    build_models(con)
    rows = con.execute(render(NAME_CHECK.read_text(encoding="utf-8"))).fetchall()
    assert rows == [("prefix_matches_no_member", "tdrss", None, None, "TDRS")]
    assert not [k for k in memberships(con) if k[1] == "tdrss"]       # no member meets the prefix


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
