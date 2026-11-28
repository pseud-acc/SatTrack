"""Integration tests: the app export (scripts/export_app_csvs.py running transform/analyses/app_export/*.sql) on a
small fixture warehouse, and the health page's data dates (scripts/build_health_page.py).

The fixture reproduces 18 Nov 2026: the enrichment mart (fct__satellite_master) is an older build, from a run
whose enrichment unit was later held, holding stale TLE lines; the tracking mart (fct__gp_elements) is from the
current run. The app must get positions and "Last updated" from tracking and the descriptive fields from
enrichment. Expected values are written out here, not computed with the code under test.
"""
from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import brotli
import duckdb
import pytest

PIPELINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PIPELINE / "ingestion"))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, PIPELINE / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


export_app_csvs = _load("export_app_csvs")
build_health_page = _load("build_health_page")

# Hand-edited, ISS-like TLE lines (catalogue 25544) at two epochs: the stale set sits in the enrichment mart, the
# fresh one in tracking. They are not real element sets (checksums not valid); the export copies them as text.
# The tracking mart's OMM element columns (gp_row) hold the fresh set's values; the export takes the numbers from
# those columns, never from the TLE text.
STALE = ("1 25544U 98067A   26320.50000000  .00016717  00000-0  10270-3 0  9990",
         "2 25544  51.6400 208.9163 0006317  69.9862  25.2906 15.49000000 10001")
FRESH = ("1 25544U 98067A   26322.13000000  .00016717  00000-0  10270-3 0  9991",
         "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50103472 10002")
OTHER = ("1 20580U 90037B   26322.10000000  .00000600  00000-0  29000-4 0  9993",
         "2 20580  28.4700 120.0000 0002500 100.0000 260.0000 15.10000000 10003")

ENRICH_RUN, ENRICH_BUILT = "run_2026-11-16T234648Z", datetime(2026, 11, 16, 23, 47, 29)
TRACK_RUN, TRACK_BUILT = "run_2026-11-18T031752Z", datetime(2026, 11, 18, 3, 18, 9)
GP_LOADED = datetime(2026, 11, 18, 3, 17, 52)
GCAT_UPDATED = datetime(2026, 11, 15, 10, 18, 40)

MASTER_COLS = ("satcat_id, object_name, object_type, flag_in_orbit, operational_status, launch_year, owner_country, "
               "site_location_country, ownership_class_labels, mission_category_labels, launch_vehicle_brand, "
               "orbit_class, orbital_period, inclination, mass_kg, tle_line_1, tle_line_2, positions_as_of, "
               "gcat_updated_at, satellite_constellation_name, primary_satellite_system_name, satellite_system_names, "
               "flag_space_station, inserted_by, inserted_date_time, "
               # the object_detail dataset's columns (D-054), ISS-like by default
               "jcat, jcat_link_method, object_type_source, operational_status_source, flag_still_operating, flag_still_transmitting, end_operation_date, end_operation_date_precision, end_transmission_date, end_transmission_date_precision, end_of_life_code, flag_orbit_conflict, owner_country_codes, owner_country_source, owner_org_codes, owner_org_names, operator_name, manufacturer_org_codes, manufacturer_org_names, launch_agency_org_codes, launch_agency_org_names, launch_datetime, launch_datetime_precision, launch_details_source, flag_catalog_match_uncertain, site_code, site_name, site_latitude, site_longitude, launch_vehicle_type, launch_vehicle_family, flight_id, satellite_program, satellite_program_family, constellation_plane, mission_details_source, apoapsis, periapsis, rcs_size, flag_mass_estimated, dry_mass_kg, span_m")


def master_row(satcat_id, **kw):
    row = dict(satcat_id=satcat_id, object_name=f"SAT {satcat_id}", object_type="PAYLOAD", flag_in_orbit=1,
               operational_status="Active", launch_year=1998, owner_country="United States",
               site_location_country="Kazakhstan", ownership_class_labels=["Government", "Civil"],
               mission_category_labels=["Space Science", "Technology"], launch_vehicle_brand="Proton",
               orbit_class="LEO", orbital_period=92.9, inclination=51.64, mass_kg=420000.0,
               tle_line_1=STALE[0], tle_line_2=STALE[1], positions_as_of=datetime(2026, 11, 16, 23, 46, 48),
               gcat_updated_at=GCAT_UPDATED, satellite_constellation_name=None,
               primary_satellite_system_name=None, satellite_system_names=[], flag_space_station=0, inserted_by=ENRICH_RUN,
               inserted_date_time=ENRICH_BUILT, jcat="S25544", jcat_link_method="s_norad", object_type_source="spacetrack", operational_status_source="gcat_psatcat", flag_still_operating=1, flag_still_transmitting=1, end_operation_date=None, end_operation_date_precision="current", end_transmission_date=None, end_transmission_date_precision="current", end_of_life_code=None, flag_orbit_conflict=0, owner_country_codes=["US", "RU"], owner_country_source="iso_exact", owner_org_codes=["NASA", "RKA"], owner_org_names=["NASA", "Roskosmos"], operator_name="NASA", manufacturer_org_codes=["KHRU"], manufacturer_org_names=["Khrunichev"], launch_agency_org_codes=["RVSN"], launch_agency_org_names=["Strategic Rocket Forces"], launch_datetime=datetime(1998, 11, 20, 6, 40), launch_datetime_precision="minute", launch_details_source="own", flag_catalog_match_uncertain=0, site_code="NIIP-5", site_name="Baikonur", site_latitude=45.92, site_longitude=63.342, launch_vehicle_type="Proton-K", launch_vehicle_family="Proton", flight_id="1998-067", satellite_program="ISS", satellite_program_family="ISS", constellation_plane=None, mission_details_source="own", apoapsis=423.8, periapsis=416.1, rcs_size="LARGE", flag_mass_estimated=0, dry_mass_kg=None, span_m=109.0)
    row.update(kw)
    return row


GP_COLS = ("satcat_id, object_id, object_name, object_type, epoch, mean_motion, eccentricity, inclination, "
           "ra_of_asc_node, arg_of_pericenter, mean_anomaly, bstar, mean_motion_dot, mean_motion_ddot, rev_at_epoch, "
           "element_set_no, ephemeris_type, classification_type, orbital_period, tle_line_1, tle_line_2, _loaded_at, "
           "inserted_by, inserted_date_time")


def gp_row(satcat_id, tle=FRESH, period=92.88, **kw):
    """The fresh ISS-like set as OMM fields (epoch 26322.13000000 = 18 Nov 2026 03:07:12)."""
    row = dict(satcat_id=satcat_id, object_id="1998-067A", object_name=f"GP {satcat_id}", object_type="PAYLOAD",
               epoch=datetime(2026, 11, 18, 3, 7, 12),
               mean_motion=15.50103472, eccentricity=0.0006703, inclination=51.6416, ra_of_asc_node=247.4627,
               arg_of_pericenter=130.536, mean_anomaly=325.0288, bstar=0.0001027, mean_motion_dot=0.00016717,
               mean_motion_ddot=0.0, rev_at_epoch=1000, element_set_no=999, ephemeris_type=0,
               classification_type="U", orbital_period=period, tle_line_1=tle[0], tle_line_2=tle[1],
               _loaded_at=GP_LOADED, inserted_by=TRACK_RUN, inserted_date_time=TRACK_BUILT)
    row.update(kw)
    return row


def build_db(path: Path, master: list[dict], gp: list[dict]) -> Path:
    con = duckdb.connect(str(path))
    con.execute("create schema marts; create schema marts_tracking")
    con.execute("""create table marts.fct__satellite_master (satcat_id integer, object_name varchar, object_type varchar,
        flag_in_orbit integer, operational_status varchar, launch_year integer, owner_country varchar,
        site_location_country varchar, ownership_class_labels varchar[], mission_category_labels varchar[],
        launch_vehicle_brand varchar, orbit_class varchar, orbital_period double, inclination double, mass_kg double,
        tle_line_1 varchar, tle_line_2 varchar, positions_as_of timestamp, gcat_updated_at timestamp,
        satellite_constellation_name varchar, primary_satellite_system_name varchar, satellite_system_names varchar[],
        flag_space_station integer, inserted_by varchar, inserted_date_time timestamp, jcat varchar, jcat_link_method varchar, object_type_source varchar, operational_status_source varchar, flag_still_operating integer, flag_still_transmitting integer, end_operation_date timestamp, end_operation_date_precision varchar, end_transmission_date timestamp, end_transmission_date_precision varchar, end_of_life_code varchar, flag_orbit_conflict integer, owner_country_codes varchar[], owner_country_source varchar, owner_org_codes varchar[], owner_org_names varchar[], operator_name varchar, manufacturer_org_codes varchar[], manufacturer_org_names varchar[], launch_agency_org_codes varchar[], launch_agency_org_names varchar[], launch_datetime timestamp, launch_datetime_precision varchar, launch_details_source varchar, flag_catalog_match_uncertain integer, site_code varchar, site_name varchar, site_latitude double, site_longitude double, launch_vehicle_type varchar, launch_vehicle_family varchar, flight_id varchar, satellite_program varchar, satellite_program_family varchar, constellation_plane varchar, mission_details_source varchar, apoapsis double, periapsis double, rcs_size varchar, flag_mass_estimated integer, dry_mass_kg double, span_m double)""")
    con.execute("""create table marts_tracking.fct__gp_elements (satcat_id integer, object_id varchar,
        object_name varchar, object_type varchar, epoch timestamp,
        mean_motion double, eccentricity double, inclination double, ra_of_asc_node double, arg_of_pericenter double,
        mean_anomaly double, bstar double, mean_motion_dot double, mean_motion_ddot double, rev_at_epoch integer,
        element_set_no integer, ephemeris_type integer, classification_type varchar, orbital_period double,
        tle_line_1 varchar, tle_line_2 varchar, _loaded_at timestamp, inserted_by varchar,
        inserted_date_time timestamp)""")
    for r in master:
        con.execute(f"insert into marts.fct__satellite_master ({MASTER_COLS}) values ({', '.join('?' * len(MASTER_COLS.split(',')))})",
                    [r[c.strip()] for c in MASTER_COLS.split(",")])
    for r in gp:
        con.execute(f"insert into marts_tracking.fct__gp_elements ({GP_COLS}) values ({', '.join('?' * 24)})",
                    [r[c.strip()] for c in GP_COLS.split(",")])
    con.close()
    return path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture
def run_export(tmp_path, monkeypatch):
    monkeypatch.setattr(export_app_csvs, "MIN_SATELLITE_ROWS", 1)   # the real floor (1,000) is for full catalogues
    for name in ("objects", "object_detail"):
        monkeypatch.setitem(export_app_csvs.DATASETS, name, {**export_app_csvs.DATASETS[name], "min_records": 1})

    def go(master, gp, out=None):
        db = build_db(tmp_path / f"wh{len(list(tmp_path.glob('wh*')))}.duckdb", master, gp)
        out = out or tmp_path / "app"
        export_app_csvs.export(out, db)
        return {f.name: f for f in out.iterdir()}
    return go


def test_positions_from_tracking_details_from_enrichment(run_export):
    files = run_export([master_row(25544, object_name="ISS (ZARYA)", owner_country="Multinational")], [gp_row(25544)])
    (row,) = read_csv(files["satcat_tle.csv"])
    # where it is: the current tracking build
    assert (row["TLE1"], row["TLE2"]) == FRESH
    assert float(row["MeanMotion"]) == 15.50103472 and float(row["Eccentricity"]) == 0.0006703
    assert float(row["OrbitalPeriod"]) == 92.88 and float(row["Inclination"]) == 51.6416   # not rounded
    # what it is: the enrichment build
    assert row["ObjectName"] == "ISS (ZARYA)" and row["Owner"] == "Multinational" and row["Status"] == "Active"
    assert row["Purpose"] == "Space Science/Technology" and row["UseType"] == "Civil/Government"
    assert row["LaunchVehicleClass"] == "Proton" and row["OrbitClass"] == "LEO" and row["LaunchYear"] == "1998"


def test_last_updated_is_the_gp_download_not_the_enrichment_build(run_export):
    files = run_export([master_row(25544)], [gp_row(25544)])
    rows = {r["Source"]: r for r in read_csv(files["last_data_update.csv"])}
    assert rows["SpaceTrack_GP"]["Last Update"] == "18/11/2026, 03:17:52"
    assert rows["SpaceTrack_GP"]["Last Download"] == "18/11/2026, 03:17:52"
    assert rows["GCAT"]["Last Update"] == "15/11/2026, 10:18:40" and rows["GCAT"]["Last Download"] == ""


def test_manifest_reports_tracking_and_details_runs(run_export):
    files = run_export([master_row(25544)], [gp_row(25544)])
    m = json.loads(files["manifest.json"].read_text(encoding="utf-8"))
    assert m["run_id"] == TRACK_RUN and m["mart_built_at"] == TRACK_BUILT.isoformat()
    assert m["positions_as_of"] == GP_LOADED.isoformat()
    assert m["details_run_id"] == ENRICH_RUN and m["details_built_at"] == ENRICH_BUILT.isoformat()
    assert m["gcat_updated_at"] == GCAT_UPDATED.isoformat()
    assert {f["file"]: f["rows"] for f in m["files"]} == {"last_data_update.csv": 2, "satcat_tle.csv": 1,
                                                          "objects.json.br": 1, "objects.json.gz": 1,
                                                          "object_detail.json.br": 1, "object_detail.json.gz": 1}


def test_scope(run_export):
    """Only Earth-orbiting payloads present in BOTH marts, with a positive period and a launch year."""
    master = [master_row(1), master_row(2), master_row(3, object_type="ROCKET BODY"), master_row(4, flag_in_orbit=0),
              master_row(5, launch_year=None), master_row(6)]
    gp = [gp_row(1), gp_row(3), gp_row(4), gp_row(5), gp_row(6, period=0.0), gp_row(7, tle=OTHER)]
    files = run_export(master, gp)
    ids = [r["SatCatId"] for r in read_csv(files["satcat_tle.csv"])]
    # 1 kept; 2 left the GP feed (decayed) -> gone; 3 not a payload; 4 not in orbit; 5 no launch year;
    # 6 non-positive period; 7 new in GP, not yet enriched -> appears after the next good enrichment build
    assert ids == ["1"]


def test_omm_elements_exported_unchanged(run_export):
    """Every field sgp4.omm.initialize reads, copied from the tracking mart: numbers unrounded, the epoch with its
    microseconds in the format sgp4.omm.initialize parses."""
    files = run_export([master_row(25544)], [gp_row(25544, epoch=datetime(2026, 11, 19, 17, 18, 6, 560064),
                                                    mean_motion_ddot=1.2345e-11, bstar=-0.00011606)])
    (row,) = read_csv(files["satcat_tle.csv"])
    assert row["Epoch"] == "2026-11-19T17:18:06.560064"
    assert datetime.strptime(row["Epoch"], "%Y-%m-%dT%H:%M:%S.%f") == datetime(2026, 11, 19, 17, 18, 6, 560064)
    numbers = ("RaOfAscNode", "ArgOfPericenter", "MeanAnomaly", "Bstar", "MeanMotionDot", "MeanMotionDdot")
    assert [float(row[k]) for k in numbers] == [247.4627, 130.536, 325.0288, -0.00011606, 0.00016717, 1.2345e-11]
    assert (row["RevAtEpoch"], row["ElementSetNo"], row["EphemerisType"]) == ("1000", "999", "0")
    assert row["ClassificationType"] == "U" and row["ObjectId"] == "1998-067A"


def test_epoch_without_fraction_keeps_the_microsecond_field(run_export):
    """A whole-second epoch still carries '.000000': sgp4.omm.initialize's format requires the fraction."""
    files = run_export([master_row(25544)], [gp_row(25544)])
    (row,) = read_csv(files["satcat_tle.csv"])
    assert row["Epoch"] == "2026-11-18T03:07:12.000000"


@pytest.mark.parametrize("field", ["object_id", "epoch", "mean_motion", "eccentricity", "inclination",
                                   "ra_of_asc_node", "arg_of_pericenter", "mean_anomaly", "bstar",
                                   "mean_motion_dot", "mean_motion_ddot", "rev_at_epoch", "element_set_no",
                                   "ephemeris_type", "classification_type"])
def test_a_satellite_without_a_full_element_set_is_left_out(run_export, field):
    files = run_export([master_row(1), master_row(2)], [gp_row(1), gp_row(2, **{field: None})])
    assert [r["SatCatId"] for r in read_csv(files["satcat_tle.csv"])] == ["1"]


def test_a_satellite_without_tle_lines_is_still_exported(run_export):
    """The app propagates from the OMM elements, so a satellite Space-Track gives no TLE lines for (e.g. a catalogue
    number above 339,999, beyond Alpha-5) is exported with empty TLE cells instead of being dropped."""
    files = run_export([master_row(1), master_row(2)], [gp_row(1), gp_row(2, tle=(None, None))])
    rows = {r["SatCatId"]: r for r in read_csv(files["satcat_tle.csv"])}
    assert set(rows) == {"1", "2"}
    assert rows["2"]["TLE1"] == "" and rows["2"]["TLE2"] == "" and rows["2"]["Epoch"] != ""
    assert rows["1"]["TLE1"] == FRESH[0]


def test_gaps_filled_so_the_app_keeps_every_row(run_export):
    """The app drops a row with any empty cell, so text gaps are 'Unknown' and number gaps -1.0."""
    files = run_export([master_row(25544, object_name=None, owner_country=None, mass_kg=None, inclination=None,
                                   ownership_class_labels=[], mission_category_labels=None)],
                       [gp_row(25544)])
    (row,) = read_csv(files["satcat_tle.csv"])
    assert row["ObjectName"] == "Unknown" and row["Owner"] == "Unknown"
    assert row["UseType"] == "Unknown" and row["Purpose"] == "Unknown" and float(row["LaunchMass"]) == -1.0
    assert all(v != "" for k, v in row.items() if k not in ("TLE1", "TLE2"))


def test_a_failed_export_keeps_the_last_good_files(run_export, monkeypatch, tmp_path):
    out = tmp_path / "app"
    first = run_export([master_row(25544)], [gp_row(25544)], out=out)
    before = {n: p.read_bytes() for n, p in first.items()}
    monkeypatch.setattr(export_app_csvs, "MIN_SATELLITE_ROWS", 1000)
    with pytest.raises(export_app_csvs.ExportError, match="only 1 rows"):
        run_export([master_row(25544)], [gp_row(25544, tle=OTHER)], out=out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before   # published files untouched, no temp files


def test_analyses_follow_the_export_rules():
    """Each analysis is documented, uses only ref() and maps to a file the app reads."""
    assert set(export_app_csvs.load_analyses()) == {"satcat_tle.csv", "last_data_update.csv", "objects",
                                                    "object_detail"}


def read_dataset(files, name="objects"):
    """Both published encodings, decoded; they must hold the same bytes."""
    br = brotli.decompress(files[f"{name}.json.br"].read_bytes())
    gz = gzip.decompress(files[f"{name}.json.gz"].read_bytes())
    assert br == gz
    return json.loads(br)


def test_objects_dataset_envelope(run_export):
    """The header every dataset carries (D-010): name, schema version, count, run, key, attribution, caution."""
    files = run_export([master_row(25544)], [gp_row(25544)])
    data = read_dataset(files)
    assert {k: data[k] for k in ("dataset", "schema", "count", "run_id", "key")} == {
        "dataset": "objects", "schema": 2, "count": 1, "run_id": TRACK_RUN, "key": "satcat_id"}
    assert any("Space-Track" in a for a in data["attribution"]) and any("GCAT" in a for a in data["attribution"])
    assert "conjunction" in data["caution"]
    assert datetime.fromisoformat(data["generated_at"]).tzinfo is not None
    assert len(data["records"]) == data["count"]


def test_objects_record_uses_warehouse_names_and_exact_elements(run_export):
    """One record per object with the marts' column names; elements exactly as in the tracking mart (D-009)."""
    files = run_export([master_row(25544, object_name="ISS (ZARYA)", ownership_class_labels=["Government", "Civil"])],
                       [gp_row(25544, epoch=datetime(2026, 11, 19, 17, 18, 6, 560064), bstar=-0.00011606)])
    (rec,) = read_dataset(files)["records"]
    assert rec == {
        "satcat_id": 25544, "object_id": "1998-067A", "object_name": "ISS (ZARYA)", "object_type": "PAYLOAD",
        "epoch": "2026-11-19T17:18:06.560064", "mean_motion": 15.50103472, "eccentricity": 0.0006703,
        "inclination": 51.6416, "ra_of_asc_node": 247.4627, "arg_of_pericenter": 130.536, "mean_anomaly": 325.0288,
        "bstar": -0.00011606, "mean_motion_dot": 0.00016717, "mean_motion_ddot": 0.0, "rev_at_epoch": 1000,
        "element_set_no": 999, "ephemeris_type": 0, "classification_type": "U", "orbital_period": 92.88,
        "operational_status": "Active", "orbit_class": "LEO", "owner_country": "United States", "launch_year": 1998,
        "mission_category_labels": ["Space Science", "Technology"], "ownership_class_labels": ["Government", "Civil"],
        "launch_vehicle_brand": "Proton", "site_location_country": "Kazakhstan", "satellite_constellation_name": None,
        "primary_satellite_system_name": None, "satellite_system_names": [],
        "flag_space_station": 0}


def test_objects_carry_constellation_and_systems_and_credit_celestrak(run_export):
    """D-047 (schema 2): the constellation, primary system and system list from the satellite mart (null / empty
    when none; a null list becomes []), and the envelope credits CelesTrak."""
    master = [master_row(44714, satellite_constellation_name="Starlink"),
              master_row(35491, primary_satellite_system_name="GOES",
                         satellite_system_names=["GOES", "Search & Rescue (SARSAT)"]),
              master_row(25544, satellite_system_names=None)]
    files = run_export(master, [gp_row(44714), gp_row(35491), gp_row(25544)])
    data = read_dataset(files)
    got = {r["satcat_id"]: (r["satellite_constellation_name"], r["primary_satellite_system_name"],
                            r["satellite_system_names"]) for r in data["records"]}
    assert got == {25544: (None, None, []), 35491: (None, "GOES", ["GOES", "Search & Rescue (SARSAT)"]),
                   44714: ("Starlink", None, [])}
    assert "constellation" not in data["records"][0]                  # schema 1's field is gone
    assert "Constellation groups: CelesTrak (Dr T.S. Kelso)" in data["attribution"]


def test_objects_flag_space_stations(run_export):
    """D-043: the space station flag from the satellite mart, 1/0, never null; an object without a satellite-mart row
    is not flagged."""
    files = run_export([master_row(25544, flag_space_station=1), master_row(44714)],
                       [gp_row(25544), gp_row(44714), gp_row(99999)])
    data = read_dataset(files)
    assert {r["satcat_id"]: r["flag_space_station"] for r in data["records"]} == {25544: 1, 44714: 0, 99999: 0}


def test_objects_cover_every_type_and_unenriched_objects(run_export):
    """Every object in the GP feed with a full element set (D-011): rocket bodies, debris and UNKNOWN too, unlike the
    payload-only CSV. An object without an enrichment row keeps Space-Track's name, null details and empty lists."""
    master = [master_row(1), master_row(2, object_type="ROCKET BODY"), master_row(3, object_type="DEBRIS",
                                                                                     mission_category_labels=None)]
    gp = [gp_row(1), gp_row(2, object_type="ROCKET BODY"), gp_row(3, object_type="DEBRIS"),
          gp_row(270449, object_type="UNKNOWN", object_id="UNKNOWN", object_name="TBA - TO BE ASSIGNED"),
          gp_row(5, epoch=None)]    # no full element set: left out
    files = run_export(master, gp)
    recs = {r["satcat_id"]: r for r in read_dataset(files)["records"]}
    assert list(recs) == [1, 2, 3, 270449]                       # sorted by key; 5 has no element set
    assert [recs[i]["object_type"] for i in recs] == ["PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"]
    assert recs[3]["mission_category_labels"] == []               # null list in the mart -> empty list
    unknown = recs[270449]
    assert unknown["object_name"] == "TBA - TO BE ASSIGNED"
    assert unknown["launch_year"] is None and unknown["owner_country"] is None
    assert unknown["mission_category_labels"] == [] and unknown["ownership_class_labels"] == []
    assert [r["SatCatId"] for r in read_csv(files["satcat_tle.csv"])] == ["1"]   # the CSV stays payloads only


def test_objects_manifest_lists_both_encodings(run_export):
    files = run_export([master_row(25544)], [gp_row(25544)])
    manifest = json.loads(files["manifest.json"].read_text(encoding="utf-8"))
    listed = {f["file"]: f for f in manifest["files"]}
    for name in ("objects.json.br", "objects.json.gz"):
        assert listed[name]["dataset"] == "objects" and listed[name]["schema"] == 2 and listed[name]["rows"] == 1
        assert listed[name]["sha256"] == export_app_csvs.sha256(files[name])


def test_a_contract_violation_keeps_the_last_good_files(run_export, tmp_path):
    """A record that breaks app/contracts/objects.schema.json (here an eccentricity of 1.5) stops the whole export:
    nothing is replaced, so the app keeps the last good, consistent set of files."""
    out = tmp_path / "app"
    first = run_export([master_row(25544)], [gp_row(25544)], out=out)
    before = {n: p.read_bytes() for n, p in first.items()}
    with pytest.raises(export_app_csvs.ExportError, match="contract violations"):
        run_export([master_row(25544)], [gp_row(25544, eccentricity=1.5)], out=out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


@pytest.mark.parametrize("name", ["objects", "object_detail"])
def test_dataset_schema_matches_the_analysis_columns(name):
    """The contract and the query can't drift: the schema requires exactly the columns the analysis selects, in the
    same names (the marts' own)."""
    import re
    schema = json.loads((export_app_csvs.CONTRACTS_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    record = schema["$defs"]["record"]
    sql = (PIPELINE / "transform" / "analyses" / "app_export" / f"app__{name}.sql").read_text(encoding="utf-8")
    final = sql[sql.index("cte_final as ("):]
    selected = re.findall(r"\bas ([a-z_]+)\s*$", final, flags=re.M)
    assert selected == record["required"]
    assert set(record["properties"]) == set(record["required"])


def test_health_page_dates(tmp_path):
    db = build_db(tmp_path / "wh.duckdb", [master_row(1), master_row(2, operational_status="Inactive")], [gp_row(1)])
    with duckdb.connect(str(db), read_only=True) as con:
        d = build_health_page.as_of(con)
    assert d["positions_as_of"] == GP_LOADED          # tracking, not the enrichment build's positions_as_of
    assert d["gcat_updated_at"] == GCAT_UPDATED
    assert (d["objects"], d["active"]) == (2, 1)


def test_object_detail_record_uses_warehouse_names(run_export):
    """D-054: the selection panel's fields with the marts' names; dates as ISO text beside their GCAT precision;
    organisations as ordered lists."""
    files = run_export([master_row(25544)], [gp_row(25544)])
    data = read_dataset(files, "object_detail")
    assert {k: data[k] for k in ("dataset", "schema", "count", "run_id", "key")} == {
        "dataset": "object_detail", "schema": 1, "count": 1, "run_id": TRACK_RUN, "key": "satcat_id"}
    assert "conjunction" in data["caution"] and any("GCAT" in a for a in data["attribution"])
    (rec,) = data["records"]
    assert rec == {
        "satcat_id": 25544, "jcat": "S25544", "jcat_link_method": "s_norad", "object_type_source": "spacetrack",
        "operational_status_source": "gcat_psatcat", "flag_still_operating": 1, "flag_still_transmitting": 1,
        "end_operation_date": None, "end_operation_date_precision": "current", "end_transmission_date": None,
        "end_transmission_date_precision": "current", "end_of_life_code": None, "flag_orbit_conflict": 0,
        "owner_country_codes": ["US", "RU"], "owner_country_source": "iso_exact",
        "owner_org_codes": ["NASA", "RKA"], "owner_org_names": ["NASA", "Roskosmos"], "operator_name": "NASA",
        "manufacturer_org_codes": ["KHRU"], "manufacturer_org_names": ["Khrunichev"],
        "launch_agency_org_codes": ["RVSN"], "launch_agency_org_names": ["Strategic Rocket Forces"],
        "launch_datetime": "1998-11-20T06:40:00", "launch_datetime_precision": "minute", "launch_details_source": "own",
        "flag_catalog_match_uncertain": 0, "site_code": "NIIP-5", "site_name": "Baikonur", "site_latitude": 45.92,
        "site_longitude": 63.342, "launch_vehicle_type": "Proton-K", "launch_vehicle_family": "Proton",
        "flight_id": "1998-067", "satellite_program": "ISS", "satellite_program_family": "ISS",
        "constellation_plane": None, "mission_details_source": "own", "apoapsis": 423.8, "periapsis": 416.1,
        "rcs_size": "LARGE", "mass_kg": 420000.0, "flag_mass_estimated": 0, "dry_mass_kg": None, "span_m": 109.0,
        "gcat_updated_at": "2026-11-15T10:18:40"}


def test_object_detail_has_the_objects_keys(run_export):
    """The panel looks a selected object up by satcat_id, so object_detail holds exactly the objects dataset's keys:
    an object without an enrichment row has null details, empty lists and 0 flags; one without a full element set
    is in neither."""
    master = [master_row(1), master_row(2, object_type="DEBRIS", owner_org_names=None, end_of_life_code="X",
                                        end_operation_date=datetime(1960, 1, 1), end_operation_date_precision="year?")]
    gp = [gp_row(1), gp_row(2, object_type="DEBRIS"), gp_row(270449, object_type="UNKNOWN"), gp_row(5, epoch=None)]
    files = run_export(master, gp)
    objects = [r["satcat_id"] for r in read_dataset(files)["records"]]
    detail = {r["satcat_id"]: r for r in read_dataset(files, "object_detail")["records"]}
    assert list(detail) == objects == [1, 2, 270449]
    assert detail[2]["owner_org_names"] == [] and detail[2]["end_of_life_code"] == "X"
    assert (detail[2]["end_operation_date"], detail[2]["end_operation_date_precision"]) == ("1960-01-01T00:00:00", "year?")
    bare = detail[270449]
    assert bare["jcat"] is None and bare["operator_name"] is None and bare["launch_datetime"] is None
    assert bare["owner_org_names"] == [] and bare["manufacturer_org_names"] == []
    assert (bare["flag_mass_estimated"], bare["flag_catalog_match_uncertain"], bare["flag_orbit_conflict"]) == (0, 0, 0)
    assert bare["flag_still_operating"] is None and bare["gcat_updated_at"] is None
