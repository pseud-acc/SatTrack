"""Unit tests: the sidebar → filter spec translation (app/helper/helper__app_data.py: sidebar_filter_spec) and the
filter table the app builds from the objects dataset at start-up (app/core/filter_spec.py, app/core/state.py, D-035).

The end-to-end result of each sidebar control (sidebar → spec → the same satellites as an independent pandas
filter) is in test_filters.py::test_filter_returns_exact_set; these tests pin the spec each control produces and
the start-up rules."""
import gzip
import json
import shutil

import pytest

from _support import ALL_ORBITS, ALL_STATUS, APP_DATA_DIR, objects_sample_ids
from app.core import filter_spec
from app.helper.helper__app_data import sidebar_filter_spec

START = dict(status=ALL_STATUS, orbit=ALL_ORBITS, satname=None, satcatid=None, owner=[], launchvehicle=[],
             purpose=[], year=[1990, 2026])


def clauses(**kw):
    spec = sidebar_filter_spec(**{**START, **kw})
    filter_spec.validate(spec)   # every spec the sidebar makes is valid
    return {c["field"]: (c["op"], c["value"]) for c in spec["clauses"]}


def test_starting_state_is_status_orbit_and_year_only():
    assert clauses() == {
        "operational_status": ("in", ["Active", "Inactive", None]),
        "orbit_class": ("in", ALL_ORBITS),
        "launch_year": ("between", {"min": 1990, "max": 2026}),
    }


def test_inactive_covers_objects_with_no_status_active_does_not():
    assert clauses(status="Active")["operational_status"] == ("in", ["Active"])
    assert clauses(status="Inactive")["operational_status"] == ("in", ["Inactive", None])
    assert clauses(status="All")["operational_status"] == ("in", ["Active", "Inactive", None])


@pytest.mark.parametrize("control, field, op", [
    ("owner", "owner_country", "in"),
    ("launchvehicle", "launch_vehicle_brand", "in"),
    ("purpose", "mission_category_labels", "contains_any"),
])
def test_multi_selects_map_unknown_to_null(control, field, op):
    assert clauses(**{control: ["France", "Unknown"]})[field] == (op, ["France", None])


def test_empty_multi_selects_add_no_clause():
    assert {"owner_country", "launch_vehicle_brand", "mission_category_labels"}.isdisjoint(clauses())


def test_one_satellite_by_name_or_number():
    assert clauses(satname="ISS (ZARYA)")["object_name"] == ("eq", "ISS (ZARYA)")
    assert clauses(satname="Unknown")["object_name"] == ("is_missing", True)
    assert clauses(satcatid="25544")["satcat_id"] == ("eq", 25544)


@pytest.mark.parametrize("empty", [{"orbit": []}, {"status": None}, {"status": "Unknown choice"}])
def test_nothing_ticked_selects_nothing(empty):
    assert sidebar_filter_spec(**{**START, **empty}) is None


def gz_entry(doc):
    return {"gzip": {"body": gzip.compress(json.dumps(doc).encode())}}


def test_filter_table_from_the_sample_dataset():
    table = filter_spec.table_from_dataset({"gzip": {"body": (APP_DATA_DIR / "objects.json.gz").read_bytes()}})
    assert set(table["satcat_id"]) == objects_sample_ids()
    assert list(table.columns) == ["satcat_id", *[f for f in filter_spec.fields() if f != "satcat_id"]]


@pytest.mark.parametrize("dataset, message", [
    (None, "objects dataset missing"),
    ({"br": {"body": b""}}, "objects dataset missing"),
    ({"gzip": {"body": b"not gzip"}}, "unreadable"),
    (gz_entry({"dataset": "objects", "count": 2, "records": [{"satcat_id": 1}]}), "envelope"),
    (gz_entry({"dataset": "object_detail", "count": 0, "records": []}), "envelope"),
])
def test_filter_table_refuses_a_missing_or_bad_dataset(dataset, message):
    with pytest.raises(filter_spec.MissingObjectsDataset, match=message):
        filter_spec.table_from_dataset(dataset)


def test_app_start_up_fails_loudly_without_the_objects_dataset(tmp_path, monkeypatch, capsys):
    """D-035: no silent fallback. A data folder without objects.json.* stops start-up with a FATAL line."""
    for name in ("satcat_tle.csv", "last_data_update.csv"):
        shutil.copy(APP_DATA_DIR / name, tmp_path / name)
    monkeypatch.setenv("SATTRACK_APP_DATA_DIR", str(tmp_path))
    from app.core import state
    with pytest.raises(filter_spec.MissingObjectsDataset):
        state.initialise_app_data()
    assert "FATAL: objects dataset missing" in capsys.readouterr().out


def test_csv_satellites_missing_from_the_dataset_are_never_shown(sample_df):
    """The 2 sample CSV satellites that aren't in the sample's objects dataset can't be selected, even by number."""
    from app.helper.helper__app_data import filter_satellite_data, sidebar_filter_spec
    table = filter_spec.table_from_dataset({"gzip": {"body": (APP_DATA_DIR / "objects.json.gz").read_bytes()}})
    absent = sorted(set(sample_df.SatCatId) - objects_sample_ids())
    assert len(absent) == 2
    out, _, _ = filter_satellite_data(sample_df.copy(), table,
                                      sidebar_filter_spec(**{**START, "satcatid": str(absent[0]), "year": [1900, 2100]}))
    assert out.empty
