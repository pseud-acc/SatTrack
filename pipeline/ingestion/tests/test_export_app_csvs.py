"""Integration tests: the app export (scripts/export_app_csvs.py running transform/analyses/app_export/*.sql) on a
small fixture warehouse, and the health page's data dates (scripts/build_health_page.py).

The fixture reproduces 18 Nov 2026: the enrichment mart (fct__satellite_master) is an older build, from a run
whose enrichment unit was later held, holding stale TLE lines; the tracking mart (fct__gp_elements) is from the
current run. The app must get positions and "Last updated" from tracking and the descriptive fields from
enrichment. Expected values are written out here, not computed with the code under test.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

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
               "gcat_updated_at, inserted_by, inserted_date_time")


def master_row(satcat_id, **kw):
    row = dict(satcat_id=satcat_id, object_name=f"SAT {satcat_id}", object_type="PAYLOAD", flag_in_orbit=1,
               operational_status="Active", launch_year=1998, owner_country="United States",
               site_location_country="Kazakhstan", ownership_class_labels=["Government", "Civil"],
               mission_category_labels=["Space Science", "Technology"], launch_vehicle_brand="Proton",
               orbit_class="LEO", orbital_period=92.9, inclination=51.64, mass_kg=420000.0,
               tle_line_1=STALE[0], tle_line_2=STALE[1], positions_as_of=datetime(2026, 11, 16, 23, 46, 48),
               gcat_updated_at=GCAT_UPDATED, inserted_by=ENRICH_RUN, inserted_date_time=ENRICH_BUILT)
    row.update(kw)
    return row


GP_COLS = ("satcat_id, object_id, epoch, mean_motion, eccentricity, inclination, ra_of_asc_node, arg_of_pericenter, "
           "mean_anomaly, bstar, mean_motion_dot, mean_motion_ddot, rev_at_epoch, element_set_no, ephemeris_type, "
           "classification_type, orbital_period, tle_line_1, tle_line_2, _loaded_at, inserted_by, inserted_date_time")


def gp_row(satcat_id, tle=FRESH, period=92.88, **kw):
    """The fresh ISS-like set as OMM fields (epoch 26322.13000000 = 18 Nov 2026 03:07:12)."""
    row = dict(satcat_id=satcat_id, object_id="1998-067A", epoch=datetime(2026, 11, 18, 3, 7, 12),
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
        inserted_by varchar, inserted_date_time timestamp)""")
    con.execute("""create table marts_tracking.fct__gp_elements (satcat_id integer, object_id varchar, epoch timestamp,
        mean_motion double, eccentricity double, inclination double, ra_of_asc_node double, arg_of_pericenter double,
        mean_anomaly double, bstar double, mean_motion_dot double, mean_motion_ddot double, rev_at_epoch integer,
        element_set_no integer, ephemeris_type integer, classification_type varchar, orbital_period double,
        tle_line_1 varchar, tle_line_2 varchar, _loaded_at timestamp, inserted_by varchar,
        inserted_date_time timestamp)""")
    for r in master:
        con.execute(f"insert into marts.fct__satellite_master ({MASTER_COLS}) values ({', '.join('?' * 21)})",
                    [r[c.strip()] for c in MASTER_COLS.split(",")])
    for r in gp:
        con.execute(f"insert into marts_tracking.fct__gp_elements ({GP_COLS}) values ({', '.join('?' * 22)})",
                    [r[c.strip()] for c in GP_COLS.split(",")])
    con.close()
    return path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture
def run_export(tmp_path, monkeypatch):
    monkeypatch.setattr(export_app_csvs, "MIN_SATELLITE_ROWS", 1)   # the real floor (1,000) is for full catalogues

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
    assert {f["file"]: f["rows"] for f in m["files"]} == {"last_data_update.csv": 2, "satcat_tle.csv": 1}


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


def test_gaps_filled_so_the_app_keeps_every_row(run_export):
    """The app drops a row with any empty cell, so text gaps are 'Unknown' and number gaps -1.0."""
    files = run_export([master_row(25544, object_name=None, owner_country=None, mass_kg=None, inclination=None,
                                   ownership_class_labels=[], mission_category_labels=None)],
                       [gp_row(25544)])
    (row,) = read_csv(files["satcat_tle.csv"])
    assert row["ObjectName"] == "Unknown" and row["Owner"] == "Unknown"
    assert row["UseType"] == "Unknown" and row["Purpose"] == "Unknown" and float(row["LaunchMass"]) == -1.0
    assert all(v != "" for v in row.values())


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
    assert set(export_app_csvs.load_analyses()) == {"satcat_tle.csv", "last_data_update.csv"}


def test_health_page_dates(tmp_path):
    db = build_db(tmp_path / "wh.duckdb", [master_row(1), master_row(2, operational_status="Inactive")], [gp_row(1)])
    with duckdb.connect(str(db), read_only=True) as con:
        d = build_health_page.as_of(con)
    assert d["positions_as_of"] == GP_LOADED          # tracking, not the enrichment build's positions_as_of
    assert d["gcat_updated_at"] == GCAT_UPDATED
    assert (d["objects"], d["active"]) == (2, 1)
