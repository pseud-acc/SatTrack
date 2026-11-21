"""Unit tests: app/helper/helper__satellite_position.py (server-side SGP4 propagation and the conversion to
latitude/longitude/altitude behind the 2D/3D views, hover labels and table).

Scope: positions equal the sgp4 library's for every sample object, built from the OMM fields (incl. Alpha-5
catalogue numbers), and agree with the TLE lines (parity); the TLE fallback for a pre-OMM file; each
object sits inside its own orbit; the TEME -> geodetic conversion uses the published GMST, returns values in
range and turns with the Earth. Not in scope: accuracy of SGP4 against reality, or an ellipsoidal Earth (the
app deliberately uses a spherical one).
"""
from datetime import timedelta

import numpy as np
import pytest

from _support import EARTH_RADIUS_KM, MU_EARTH, sgp4_teme, sgp4_teme_omm
from app.helper.helper__satellite_position import (compute_satloc, julianDateToGMST2, lla_to_xyz, satrec_sources,
                                                   satrecs_for)

OMM_COLUMNS = ["Epoch", "RaOfAscNode", "ArgOfPericenter", "MeanAnomaly", "Bstar", "MeanMotionDot", "MeanMotionDdot",
               "RevAtEpoch", "ElementSetNo", "EphemerisType", "ClassificationType", "ObjectId"]


def positions(df, when):
    return compute_satloc(satrecs_for(df), when, EARTH_RADIUS_KM, False)


def test_positions_equal_sgp4_and_failures_are_nan(sample_df, t_ref):
    """Every row: same TEME position as sgp4 built from the row's OMM fields (to 1 mm); a row sgp4 can't
    propagate is all-NaN, which is what the app's dropna() relies on to hide it."""
    out = positions(sample_df, t_ref)
    assert out.shape == (len(sample_df), 6)
    for i, row in sample_df.iterrows():
        ref = sgp4_teme_omm(row, t_ref)
        if ref is None:
            assert np.isnan(out[i]).all(), f"row {i}: sgp4 error but the app returned a position"
        else:
            np.testing.assert_allclose(out[i, :3], ref, atol=1e-6, err_msg=f"row {i}")


def test_app_propagates_from_omm(sample_df):
    assert satrec_sources(sample_df) == {"omm": len(sample_df), "tle": 0, "none": 0}


@pytest.mark.parametrize("hours", [-24, 0, 24])
def test_omm_and_tle_positions_agree(sample_df, t_ref, hours):
    """Parity (plan 1.3/1.4): the app's OMM positions vs sgp4 from the same rows' TLE lines, for every sample object
    (incl. Alpha-5) at the reference time and a day either side. The sample's OMM fields carry the TLE's precision,
    so they agree to centimetres; 10 m allows for that. (On live data, where OMM has one more digit of eccentricity
    and more of B*, they differed by at most 29 m on 21 Nov 2026.)"""
    when = t_ref + timedelta(hours=hours)
    out = positions(sample_df, when)
    for i, (tle1, tle2) in enumerate(sample_df[["TLE1", "TLE2"]].values):
        ref = sgp4_teme(tle1, tle2, when)
        if ref is None:
            continue
        assert np.linalg.norm(out[i, :3] - ref) < 0.010, f"row {i}"


def test_tle_fallback_for_a_file_without_omm_columns(sample_df, t_ref):
    """A pre-OMM satcat_tle.csv (17 columns) still works for one release: positions from the TLE lines."""
    old = sample_df.drop(columns=OMM_COLUMNS)
    assert satrec_sources(old) == {"omm": 0, "tle": len(old), "none": 0}
    out = positions(old, t_ref)
    for i, (tle1, tle2) in enumerate(old[["TLE1", "TLE2"]].values):
        np.testing.assert_allclose(out[i, :3], sgp4_teme(tle1, tle2, t_ref), atol=1e-6, err_msg=f"row {i}")


def test_a_row_without_any_element_set_has_no_position(sample_df, t_ref):
    df = sample_df.head(3).copy()
    df.loc[1, ["Epoch", "TLE1", "TLE2"]] = np.nan          # incomplete OMM and no TLE
    df.loc[2, "Bstar"] = np.nan                              # incomplete OMM -> TLE fallback
    assert satrec_sources(df) == {"omm": 1, "tle": 1, "none": 1}
    out = positions(df, t_ref)
    assert np.isnan(out[1]).all()
    assert not np.isnan(out[[0, 2]]).any()


def test_each_element_set_is_built_once(sample_df):
    """Callbacks reuse the Satrec built for an element set; a new epoch for the same satellite gets a new one."""
    first = satrecs_for(sample_df.head(2))
    again = satrecs_for(sample_df.head(2))
    assert all(a is b for a, b in zip(first, again))
    newer = sample_df.head(1).copy()
    newer.loc[0, "Epoch"] = "2030-01-01T00:00:00.000000"
    assert satrecs_for(newer)[0] is not first[0]


def test_rows_without_elements_do_not_grow_the_cache(sample_df):
    """A row with no element set is cached under one key, not a new NaN key on every callback."""
    from app.helper import helper__satellite_position as sp
    df = sample_df.head(1).copy()
    df.loc[0, ["Epoch", "TLE1", "TLE2"]] = np.nan
    satrecs_for(df)
    size = len(sp._satrec_cache)
    for _ in range(3):
        assert satrecs_for(df) == [None]
    assert len(sp._satrec_cache) == size


def test_sample_propagates_at_reference_time(sample_df, t_ref):
    """Guards the sample, not the app: at its own download time every object should propagate. If this
    fails, the sample needs re-cutting (otherwise the other tests silently cover fewer objects)."""
    assert not np.isnan(positions(sample_df, t_ref)).any()


def test_alpha5_catalogue_numbers_decode(sample_df, t_ref):
    """Objects above 99,999 use Alpha-5 TLE lines (e.g. 'A0551' = 100551). sgp4 must decode each to the
    catalogue number the pipeline exported, and the app must propagate it (from OMM, where the catalogue number
    is a plain integer)."""
    from sgp4.api import Satrec
    alpha5 = sample_df[sample_df["SatCatId"] > 99_999]
    assert len(alpha5) >= 1, "the sample must keep Alpha-5 objects"
    for (tle1, tle2), satcat in zip(alpha5[["TLE1", "TLE2"]].values, alpha5["SatCatId"]):
        assert tle1[2].isalpha()
        assert Satrec.twoline2rv(tle1, tle2).satnum == satcat
    assert not np.isnan(positions(alpha5, t_ref)).any()


def test_every_object_within_its_own_orbit(sample_df, t_ref):
    """Distance from Earth's centre lies between perigee a(1-e) and apogee a(1+e), with a from the mean
    motion (Kepler's third law). 1% tolerance covers SGP4's periodic terms and the mean-element definition."""
    out = positions(sample_df, t_ref)
    n = sample_df["MeanMotion"].to_numpy() * 2 * np.pi / 86400   # rev/day -> rad/s
    a = (MU_EARTH / n**2) ** (1 / 3)
    e = sample_df["Eccentricity"].to_numpy()
    radius = out[:, 5] + EARTH_RADIUS_KM
    assert np.all(radius >= a * (1 - e) * 0.99)
    assert np.all(radius <= a * (1 + e) * 1.01)
    np.testing.assert_allclose(radius, np.linalg.norm(out[:, :3], axis=1), rtol=1e-12)  # alt = |r| - Re


def test_gmst_at_j2000_matches_published_value():
    """GMST at J2000.0 (2000-01-01 12:00 UT1) is 280.46061837 deg: 18.697374558 h in the US Naval
    Observatory's GMST formula (https://aa.usno.navy.mil/faq/GAST)."""
    theta, _ = julianDateToGMST2(2451545.0, 0.0)
    assert np.degrees(theta) % 360 == pytest.approx(280.46061837, abs=1e-6)


def test_latitude_is_geocentric(sample_df, t_ref):
    out = positions(sample_df, t_ref)
    r = np.linalg.norm(out[:, :3], axis=1)
    np.testing.assert_allclose(out[:, 3], np.degrees(np.arcsin(out[:, 2] / r)), atol=1e-9)
    assert np.all(np.abs(out[:, 3]) <= 90)


def test_longitude_within_180_over_a_day(sample_df, t_ref):
    """Hover labels, the table and its CSV export print this value, so it must be in [-180, 180]. GMST can be up
    to 720 deg, so a single +/-360 step isn't enough (values reached -405 deg before the fix)."""
    for hour in range(24):
        lon = positions(sample_df, t_ref + timedelta(hours=hour))[:, 4]
        assert np.all((lon >= -180) & (lon <= 180)), f"hour {hour}: min {lon.min():.1f}, max {lon.max():.1f}"


def test_geostationary_satellites_hold_longitude(sample_df, t_ref):
    """Active, near-circular, near-equatorial GEO satellites stay over one longitude: over 24 h each moves
    less than 0.3 deg. A wrong Earth-rotation rate (e.g. a solar instead of a sidereal day, ~1 deg/day)
    fails this."""
    geo = sample_df[(sample_df["OrbitClass"] == "GEO") & (sample_df["Status"] == "Active")
                    & (sample_df["Inclination"] < 0.5) & (sample_df["Eccentricity"] < 0.001)]
    assert len(geo) >= 5, "the sample needs station-kept GEO satellites for this check"
    lon0 = positions(geo, t_ref)[:, 4]
    lon1 = positions(geo, t_ref + timedelta(hours=24))[:, 4]
    drift = (lon1 - lon0 + 180) % 360 - 180   # compare angles, not raw values
    assert np.all(np.abs(drift) < 0.3), f"max drift {np.abs(drift).max():.3f} deg"


def test_time_series_equals_sgp4_at_each_time(sample_df, t_ref):
    """The orbit-path branch (one satellite, many times) matches sgp4 point by point."""
    row = sample_df.iloc[0]
    times = [t_ref + timedelta(minutes=m) for m in range(0, 120, 10)]
    for eci in (True, False):
        out = compute_satloc(satrecs_for(sample_df.iloc[[0]])[0], times, EARTH_RADIUS_KM, eci)
        assert out.shape == (len(times), 6)
        for k, when in enumerate(times):
            np.testing.assert_allclose(out[k, :3], sgp4_teme_omm(row, when), atol=1e-6)


def test_longitude_wrap_keeps_the_direction():
    """Wrapping changes the number, never the direction: each wrapped value differs from the input by a whole
    number of turns."""
    from app.helper.helper__satellite_position import longitude_trunc
    raw = np.radians(np.array([-719.9, -405.1, -270.0, -180.0, -1.0, 0.0, 179.9, 180.0, 540.0]))
    wrapped = longitude_trunc(raw)
    assert np.all((wrapped >= -np.pi) & (wrapped < np.pi))
    turns = (raw - wrapped) / (2 * np.pi)
    np.testing.assert_allclose(turns, np.round(turns), atol=1e-9)


def test_lla_to_xyz_preserves_radius_and_direction():
    lat = np.array([0.0, 45.0, -60.0, 90.0])
    lon = np.array([0.0, 90.0, -120.0, 0.0])
    alt = np.array([400.0, 20200.0, 35786.0, 1000.0])
    x, y, z = lla_to_xyz(lat, lon, alt, EARTH_RADIUS_KM)
    np.testing.assert_allclose(np.sqrt(x**2 + y**2 + z**2), alt + EARTH_RADIUS_KM, rtol=1e-12)
    np.testing.assert_allclose(np.degrees(np.arcsin(z / (alt + EARTH_RADIUS_KM))), lat, atol=1e-9)
    # -270 deg and 90 deg are the same direction: the 3D view is unaffected by the longitude bug
    a = np.array(lla_to_xyz(np.array([10.0]), np.array([-270.0]), np.array([500.0]), EARTH_RADIUS_KM))
    b = np.array(lla_to_xyz(np.array([10.0]), np.array([90.0]), np.array([500.0]), EARTH_RADIUS_KM))
    np.testing.assert_allclose(a, b, atol=1e-6)
