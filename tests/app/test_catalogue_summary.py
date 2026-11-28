"""Unit tests: app/core/catalogue_summary.build_summary, called directly on hand-made records. Every expected
figure is written out here.

Scope: the totals by type and status; the six views count working satellites only (active payloads), ranked by
count then name; a satellite in two systems or missions counts in each but once in "satellites"; operators come from
object_detail; the records strip's four figures; no detail dataset gives no operators and no strip; well-known
objects are offered only when present.
"""
from app.core.catalogue_summary import VIEWS, WELL_KNOWN, build_summary


def obj(satcat_id, kind="PAYLOAD", status="Active", **kw):
    r = {"satcat_id": satcat_id, "object_type": kind, "operational_status": status,
         "satellite_constellation_name": None, "satellite_system_names": [], "owner_country": None,
         "mission_category_labels": [], "orbit_class": "LEO"}
    r.update(kw)
    return r


def det(satcat_id, **kw):
    d = {"satcat_id": satcat_id, "operator_name": None, "owner_org_names": [], "flag_still_operating": None,
         "flag_still_transmitting": None, "flag_mass_estimated": 0, "flag_catalog_match_uncertain": 0}
    d.update(kw)
    return d


OBJECTS = [
    obj(1, satellite_constellation_name="Starlink", owner_country="United States",
        mission_category_labels=["Communications"]),
    obj(2, satellite_constellation_name="Starlink", owner_country="United States",
        mission_category_labels=["Communications"]),
    obj(3, satellite_constellation_name="OneWeb", owner_country="United Kingdom",
        mission_category_labels=["Communications"]),
    obj(4, satellite_system_names=["GOES", "Search & Rescue (SARSAT)"], owner_country="United States",
        mission_category_labels=["Meteorology (imaging)", "Communications"], orbit_class="GEO"),
    obj(5, satellite_system_names=["GPS"], owner_country=None, orbit_class="MEO"),
    obj(6, status="Inactive", satellite_constellation_name="Starlink", owner_country="United States"),   # not working
    obj(7, status=None, owner_country="France"),                                                         # no status
    obj(8, kind="ROCKET BODY", status="Inactive", owner_country="China"),
    obj(9, kind="DEBRIS", status="Inactive"),
    obj(10, kind="DEBRIS", status="Inactive"),
    obj(11, kind="UNKNOWN", status=None, orbit_class=None),
    obj(25544, owner_country="United States", orbit_class="LEO"),
]
DETAILS = [
    det(1, operator_name="SpaceX", owner_org_names=["SpaceX"]),
    det(2, operator_name="SpaceX", owner_org_names=["SpaceX"], flag_mass_estimated=1),
    det(3, operator_name="OneWeb", owner_org_names=["OneWeb", "Eutelsat"]),
    det(4, operator_name="NOAA", owner_org_names=["NOAA", "NASA"], flag_catalog_match_uncertain=1),
    det(5),
    det(6, operator_name="SpaceX", flag_still_operating=0, flag_still_transmitting=1, flag_mass_estimated=1),
    det(7, flag_still_operating=0, flag_still_transmitting=0),
    det(8, flag_mass_estimated=1), det(9), det(10), det(11),
    det(25544, operator_name="NASA", owner_org_names=["NASA", "Roskosmos", "ESA"]),
]


def names(view):
    return [(e["name"], e["count"]) for e in view["entries"]]


def test_totals():
    s = build_summary(OBJECTS, DETAILS)
    assert s["totals"] == {"tracked": 12, "working": 6, "inactive": 2, "rocket_bodies": 1, "debris": 2}


def test_views_count_working_satellites_only_ranked_by_count_then_name():
    v = build_summary(OBJECTS, DETAILS)["views"]
    assert list(v) == list(VIEWS)
    assert names(v["constellations"]) == [("Starlink", 2), ("OneWeb", 1)]          # the inactive Starlink isn't counted
    assert names(v["systems"]) == [("GOES", 1), ("GPS", 1), ("Search & Rescue (SARSAT)", 1)]   # ties by name
    assert names(v["countries"]) == [("United States", 4), ("United Kingdom", 1)]
    assert names(v["missions"]) == [("Communications", 4), ("Meteorology (imaging)", 1)]
    assert names(v["orbits"]) == [("LEO", 4), ("GEO", 1), ("MEO", 1)]
    assert names(v["operators"]) == [("SpaceX", 2), ("NASA", 1), ("NOAA", 1), ("OneWeb", 1)]


def test_groups_and_satellites_with_a_value():
    v = build_summary(OBJECTS, DETAILS)["views"]
    assert (v["constellations"]["groups"], v["constellations"]["satellites"]) == (2, 3)
    assert (v["systems"]["groups"], v["systems"]["satellites"]) == (3, 2)        # one satellite is in two systems
    assert (v["missions"]["groups"], v["missions"]["satellites"]) == (2, 4)
    assert (v["countries"]["groups"], v["countries"]["satellites"]) == (2, 5)    # one working satellite has no country
    assert (v["operators"]["groups"], v["operators"]["satellites"]) == (4, 5)
    assert v["orbits"]["satellites"] == 6


def test_records_strip_counts_every_object_with_a_detail_record():
    r = build_summary(OBJECTS, DETAILS)["records"]
    assert r == {"still_transmitting": 1, "several_owners": 3, "estimated_mass": 3, "uncertain_match": 1}


def test_without_the_detail_dataset_there_are_no_operators_and_no_strip():
    for details in (None, []):
        s = build_summary(OBJECTS, details)
        assert s["records"] is None
        assert s["views"]["operators"] == {"entries": [], "groups": 0, "satellites": 0}
        assert names(s["views"]["constellations"]) == [("Starlink", 2), ("OneWeb", 1)]   # the rest is unaffected


def test_well_known_objects_only_when_present():
    assert build_summary(OBJECTS, DETAILS)["well_known"] == [
        {"satcat_id": 25544, "name": WELL_KNOWN[25544]}]
    assert build_summary([o for o in OBJECTS if o["satcat_id"] != 25544], DETAILS)["well_known"] == []


def test_an_empty_catalogue():
    s = build_summary([], None)
    assert s["totals"] == {"tracked": 0, "working": 0, "inactive": 0, "rocket_bodies": 0, "debris": 0}
    assert all(v == {"entries": [], "groups": 0, "satellites": 0} for v in s["views"].values())
