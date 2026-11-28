"""Unit tests: the list view's helpers, called directly (owner, 27 Nov 2026: every object type in the list).

- helper__app_data.list_objects: the objects a spec selects, from the objects dataset, placed at the current time;
  objects SGP4 can't place are left out; a None spec selects nothing.
- helper__table_display.format_table_data: the documented columns in order, the Type label, "Not yet named
  (designator)" for objects Space-Track hasn't named, rounding, sorting and nulls.
- helper__satellite_position.satrecs_for with the objects dataset's field names: the same positions as the sgp4
  library built from each record (parity, to 1 mm), for every object type.
Expected values are written out here or come from the sgp4 library, never from the app's helpers.
"""
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from _support import EARTH_RADIUS_KM, objects_sample, sgp4_teme_object
from app.core import filter_spec
from app.helper.helper__app_data import list_objects
from app.helper.helper__satellite_position import OMM_FIELDS, OMM_FIELDS_OBJECTS, compute_satloc, satrec_sources, satrecs_for
from app.helper.helper__table_display import create_table_mapping, format_table_data


@pytest.fixture(scope="module")
def objects():
    return objects_sample()


def test_objects_field_names_are_the_omm_keywords_in_lower_case():
    assert set(OMM_FIELDS_OBJECTS) == set(OMM_FIELDS)
    assert OMM_FIELDS_OBJECTS["NORAD_CAT_ID"] == "satcat_id"
    assert all(v == k.lower() for k, v in OMM_FIELDS_OBJECTS.items() if k != "NORAD_CAT_ID")


def test_positions_from_the_objects_dataset_equal_sgp4_for_every_type(objects, t_ref):
    """Parity: every sample object, of every type, sits where the sgp4 library puts it (to 1 mm); an object sgp4
    can't place is all-NaN."""
    out = compute_satloc(satrecs_for(objects, OMM_FIELDS_OBJECTS), t_ref, EARTH_RADIUS_KM, False)
    assert out.shape == (len(objects), 6)
    assert set(objects["object_type"]) == {"PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"}
    for i, rec in enumerate(objects.to_dict("records")):
        ref = sgp4_teme_object(rec, t_ref)
        if ref is None:
            assert np.isnan(out[i]).all(), rec["satcat_id"]
        else:
            np.testing.assert_allclose(out[i, :3], ref, atol=1e-6, err_msg=str(rec["satcat_id"]))
    assert satrec_sources(objects, OMM_FIELDS_OBJECTS) == {"omm": len(objects), "tle": 0, "none": 0}


def test_each_objects_element_set_is_built_once(objects):
    first = satrecs_for(objects, OMM_FIELDS_OBJECTS)
    again = satrecs_for(objects, OMM_FIELDS_OBJECTS)
    assert all(a is b for a, b in zip(first, again))


def spec_for(types):
    return {"version": 1, "clauses": [{"field": "object_type", "op": "in", "value": types}]}


def test_list_objects_selects_by_the_spec_and_places_them(objects, t_ref, frozen_clock):
    table = filter_spec.table_from_records(objects.to_dict("records"))
    dff, when = list_objects(objects, table, spec_for(["DEBRIS", "ROCKET BODY"]))
    assert when == t_ref
    want = {r["satcat_id"] for r in objects.to_dict("records")
            if r["object_type"] in ("DEBRIS", "ROCKET BODY") and sgp4_teme_object(r, t_ref) is not None}
    assert len(want) > 0 and set(dff["satcat_id"]) == want
    assert dff[["lat", "lon", "alt"]].notna().all().all()
    assert dff["lat"].between(-90, 90).all() and dff["lon"].between(-180, 180).all()


def test_list_objects_with_no_spec_selects_nothing(objects, frozen_clock):
    table = filter_spec.table_from_records(objects.to_dict("records"))
    dff, _ = list_objects(objects, table, None)
    assert len(dff) == 0


def test_list_objects_leaves_out_what_sgp4_cannot_place(objects, t_ref, frozen_clock):
    """An element set SGP4 rejects (eccentricity above 1) has no row, as on the globe."""
    bad = objects.iloc[[0]].copy()
    bad["satcat_id"], bad["eccentricity"] = 999_001, 1.2
    both = pd.concat([objects.iloc[[1]], bad], ignore_index=True)
    table = filter_spec.table_from_records(both.to_dict("records"))
    dff, _ = list_objects(both, table, {"version": 1, "clauses": []})
    assert list(dff["satcat_id"]) == [int(objects.iloc[1]["satcat_id"])]


def frame(**overrides):
    row = {"object_name": "ALPHA", "object_id": "2020-001A", "object_type": "PAYLOAD", "satcat_id": 45001,
           "operational_status": "Active", "orbit_class": "LEO", "launch_year": 2020, "owner_country": "France",
           "lat": 12.3456, "lon": -45.6789, "alt": 549.6}
    return {**row, **overrides}


def test_format_table_data_columns_labels_and_rounding():
    when = datetime(2026, 11, 28, 3, 4, 5)
    rows = format_table_data(pd.DataFrame([
        frame(),
        frame(object_name="ZETA DEB", object_type="DEBRIS", satcat_id=45003, operational_status=None, launch_year=None,
              owner_country=None),
        frame(object_name="TBA - TO BE ASSIGNED", object_id="2026-090C", object_type="ROCKET BODY", satcat_id=45002),
        frame(object_name="TBA - TO BE ASSIGNED", object_id=None, object_type="UNKNOWN", satcat_id=45004),
    ]), when)
    assert [list(r) for r in rows] == [list(create_table_mapping().values())] * 4
    assert list(create_table_mapping().values()) == [
        "Name", "Type", "SATCAT Number", "Status", "Orbit", "Year of Launch", "Owner", "Latitude", "Longitude",
        "Altitude (km)", "Datetime (UTC)"]
    assert [r["Name"] for r in rows] == ["ALPHA", "Not yet named (2026-090C)", "Not yet named (?)", "ZETA DEB"]   # sorted
    assert [r["Type"] for r in rows] == ["Payload", "Rocket body", "UNKNOWN", "Debris"]
    first, debris = rows[0], rows[3]
    assert (first["Latitude"], first["Longitude"], first["Altitude (km)"]) == (12.35, -45.68, 550)
    assert first["Year of Launch"] == 2020 and first["Datetime (UTC)"] == "03:04:05, 28/11/2026"
    assert debris["Status"] is None and debris["Year of Launch"] is None and debris["Owner"] is None   # gaps stay empty
