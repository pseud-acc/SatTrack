"""Callback tests: the list view (update_tbl in app/callbacks/callback_table.py), through
/_dash-update-component, starting from the page's own sidebar values.

Scope: the table holds exactly the expected objects of every type the filters ask for (owner, 27 Nov 2026: rocket
bodies and debris too), from the objects dataset, sorted by name, with the documented columns (a Type column
included) and the time of the positions; it is built only while its tab is open, and opening the tab again with
unchanged filters sends nothing (D-052). Expected rows come from plain pandas over the sample's objects dataset and
the sgp4 library, never from the app's helpers.
"""
import pytest

from _support import expected_object_ids, objects_sample

OUT = "tab-list-body"
BODY, SHOWN = f"{OUT}.children", "list-shown-spec.data"
TAB = {"sat-viz-tabs.active_tab": "tbl-viz"}
TYPES, STATUS = "type-filter-checkbox.value", "status-filter-checkbox.value"
COLUMNS = ["Name", "Type", "SATCAT Number", "Status", "Orbit", "Year of Launch", "Owner", "Latitude", "Longitude",
           "Altitude (km)", "Datetime (UTC)"]
TYPE_NAMES = {"PAYLOAD": "Payload", "ROCKET BODY": "Rocket body", "DEBRIS": "Debris"}


@pytest.fixture(scope="module")
def objects():
    return objects_sample()


def table_rows(out):
    """The DataTable's rows from the tab's contents (its first child, id satellite-list)."""
    table = out[BODY][0]
    assert table["props"]["id"] == "satellite-list"
    return table["props"]["data"]


@pytest.mark.parametrize("values, expect", [
    ({}, dict()),
    ({"orbit-filter-checkbox.value": ["GSO"]}, dict(orbit=["GSO"])),
    ({TYPES: ["PAYLOAD", "ROCKET BODY", "DEBRIS"], STATUS: "All"},
     dict(status="All", types=["PAYLOAD", "ROCKET BODY", "DEBRIS"])),
    ({TYPES: ["DEBRIS"], STATUS: "Inactive"}, dict(status="Inactive", types=["DEBRIS"])),
], ids=["start", "GSO", "every type", "debris only"])
def test_table_rows_and_columns(callbacks, objects, t_ref, values, expect):
    status, out = callbacks.call(OUT, next(iter(values), "orbit-filter-checkbox.value"), **{**TAB, **values})
    assert status == 200
    rows = table_rows(out)
    assert all(list(r) == COLUMNS for r in rows)
    expected = expected_object_ids(objects, t_ref, **expect)
    assert len(expected) > 0
    assert {r["SATCAT Number"] for r in rows} == expected
    by_id = objects.set_index("satcat_id")
    assert all(r["Type"] == TYPE_NAMES[by_id.loc[r["SATCAT Number"], "object_type"]] for r in rows)
    names = [r["Name"] for r in rows]
    assert names == sorted(names)
    assert {r["Datetime (UTC)"] for r in rows} == {t_ref.strftime("%H:%M:%S, %d/%m/%Y")}


def test_every_type_lists_rocket_bodies_and_debris(callbacks, objects, t_ref):
    """The point of the change: with the junk types switched on, the list holds them (the app CSV has payloads only)."""
    status, out = callbacks.call(OUT, TYPES, **{**TAB, TYPES: ["PAYLOAD", "ROCKET BODY", "DEBRIS"], STATUS: "All"})
    assert status == 200
    counts = {}
    for r in table_rows(out):
        counts[r["Type"]] = counts.get(r["Type"], 0) + 1
    for kind, name in TYPE_NAMES.items():
        want = len(expected_object_ids(objects, t_ref, status="All", types=[kind]))
        assert want > 0 and counts.get(name, 0) == want, kind


def test_a_row_shows_the_objects_own_fields_and_a_position_in_range(callbacks, objects):
    status, out = callbacks.call(OUT, "orbit-filter-checkbox.value", **TAB)
    assert status == 200
    by_id = objects.set_index("satcat_id")
    for r in table_rows(out):
        rec = by_id.loc[r["SATCAT Number"]]
        assert r["Name"] == rec["object_name"] and r["Status"] == rec["operational_status"]
        assert r["Orbit"] == rec["orbit_class"] and r["Year of Launch"] == rec["launch_year"]
        assert r["Owner"] == rec["owner_country"] or (r["Owner"] is None and rec["owner_country"] is None)
        assert -90 <= r["Latitude"] <= 90 and -180 <= r["Longitude"] <= 180 and r["Altitude (km)"] > 100


@pytest.mark.parametrize("tab", ["globe", "2d-viz"])
def test_other_tabs_do_not_run_it(callbacks, tab):
    status, _ = callbacks.call(OUT, "orbit-filter-checkbox.value", **{"sat-viz-tabs.active_tab": tab})
    assert status == 204


def test_reopening_with_the_same_filters_sends_nothing(callbacks):
    """Owner, 27 Nov 2026: every tab switch rebuilt the list (~4 MB). The spec it was built for is kept; opening the
    tab again with that spec is a no-op, and a changed spec rebuilds it."""
    status, out = callbacks.call(OUT, "sat-viz-tabs.active_tab", **TAB)
    assert status == 200 and out[SHOWN]["spec"]
    status, _ = callbacks.call(OUT, "sat-viz-tabs.active_tab",
                               **{**TAB, SHOWN: out[SHOWN], "filter-spec.data": out[SHOWN]["spec"]})
    assert status == 204
    status, again = callbacks.call(OUT, "orbit-filter-checkbox.value",
                                   **{**TAB, SHOWN: out[SHOWN], "orbit-filter-checkbox.value": ["GSO"]})
    assert status == 200 and again[SHOWN] != out[SHOWN]
