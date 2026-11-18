"""Unit tests: app/helper/helper__satellite_position.py (server-side SGP4 propagation and the conversion to
latitude/longitude/altitude behind the 2D/3D views, hover labels and table).

Scope: positions equal the sgp4 library's for every sample object (incl. Alpha-5 catalogue numbers); each
object sits inside its own orbit; the TEME -> geodetic conversion uses the published GMST, returns values in
range and turns with the Earth. Not in scope: accuracy of SGP4 against reality, or an ellipsoidal Earth (the
app deliberately uses a spherical one).
"""
from datetime import timedelta

import numpy as np
import pytest

from _support import EARTH_RADIUS_KM, MU_EARTH, sgp4_teme
from app.helper.helper__satellite_position import compute_satloc, julianDateToGMST2, lla_to_xyz


def positions(df, when):
    return compute_satloc(df[["TLE1", "TLE2"]].values, when, EARTH_RADIUS_KM, False)


def test_positions_equal_sgp4_and_failures_are_nan(sample_df, t_ref):
    """Every row: same TEME position as sgp4 directly (to 1 mm); a row sgp4 can't propagate is all-NaN,
    which is what the app's dropna() relies on to hide it."""
    out = positions(sample_df, t_ref)
    assert out.shape == (len(sample_df), 6)
    for i, (tle1, tle2) in enumerate(sample_df[["TLE1", "TLE2"]].values):
        ref = sgp4_teme(tle1, tle2, t_ref)
        if ref is None:
            assert np.isnan(out[i]).all(), f"row {i}: sgp4 error but the app returned a position"
        else:
            np.testing.assert_allclose(out[i, :3], ref, atol=1e-6, err_msg=f"row {i}")


def test_sample_propagates_at_reference_time(sample_df, t_ref):
    """Guards the sample, not the app: at its own download time every object should propagate. If this
    fails, the sample needs re-cutting (otherwise the other tests silently cover fewer objects)."""
    assert not np.isnan(positions(sample_df, t_ref)).any()


def test_alpha5_catalogue_numbers_decode(sample_df, t_ref):
    """Objects above 99,999 use Alpha-5 TLE lines (e.g. 'A0551' = 100551). sgp4 must decode each to the
    catalogue number the pipeline exported, and the app must propagate it."""
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


@pytest.mark.xfail(strict=True, reason="Bug: longitude_trunc wraps once but GMST can be up to 720 deg, so "
                                       "longitudes reach -405 deg. Fixed in fix/longitude-range; remove this mark "
                                       "there (strict: the run fails once the fix makes this pass).")
def test_longitude_within_180_over_a_day(sample_df, t_ref):
    """Hover labels, the table and its CSV export print this value, so it must be in [-180, 180]."""
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
        out = compute_satloc(np.array([row["TLE1"], row["TLE2"]]), times, EARTH_RADIUS_KM, eci)
        assert out.shape == (len(times), 6)
        for k, when in enumerate(times):
            np.testing.assert_allclose(out[k, :3], sgp4_teme(row["TLE1"], row["TLE2"], when), atol=1e-6)


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
