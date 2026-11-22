"""Unit tests: app/helper/helper__app_data.py (sidebar filter options, applying the sidebar's values, orbit
paths).

Scope: each sidebar control, and one combination, returns exactly the satellites an independent pandas filter
selects (minus objects sgp4 can't propagate). This is the baseline the roadmap's filter spec (2.2/2.3) must
reproduce. Positions themselves are covered in test_satellite_position.py.
"""


import numpy as np
import pytest

from _support import ALL_ORBITS, ALL_STATUS, EARTH_RADIUS_KM, expected_ids
from app.helper.helper__app_data import create_data_filters, filter_satellite_data, generate_orbital_path
from app.helper.helper__satellite_position import compute_satloc, satrecs_for


@pytest.fixture(scope="module")
def filters(sample_df):
    return create_data_filters(sample_df.copy())


def run(df, filters, **kw):
    """filter_satellite_data with the sidebar's starting values (everything selected), overridden by kw."""
    options, init_filter = filters
    args = dict(status=ALL_STATUS, orbit=ALL_ORBITS, satname=None, satcatid=None, owner=[], launchvehicle=[],
                purpose=[], year=list(options["launchyear"]))
    args.update(kw)
    out, time_now, encoded = filter_satellite_data(df.copy(), init_filter, **args)
    return out, time_now, encoded, args


def test_options_built_from_the_data(sample_df, filters):
    options, _ = filters
    assert options["orbit"] == ALL_ORBITS
    assert list(options["launchyear"]) == [sample_df.LaunchYear.min(), sample_df.LaunchYear.max()]
    assert options["owner"] == sorted(sample_df.Owner.unique())
    assert options["launchvehicle"] == sorted(sample_df.LaunchVehicleClass.unique())
    assert options["purpose"] == sorted({p for v in sample_df.Purpose for p in v.split("/")})
    assert options["satname"] == sorted(sample_df.ObjectName.unique())
    assert sorted(options["satcatid"], key=int) == [str(i) for i in sorted(sample_df.SatCatId.unique())]


def test_uses_the_app_clock(sample_df, filters, t_ref):
    _, time_now, _, _ = run(sample_df, filters)
    assert time_now == t_ref   # the frozen clock reached the app; positions below are for t_ref


@pytest.mark.parametrize("case", [
    {},                                                  # starting state: everything
    {"status": ["Active"]},
    {"status": ["Inactive"]},
    {"status": []},                                      # nothing ticked -> nothing shown
    {"orbit": ["GEO"]},
    {"orbit": ["LEO", "HEO"]},
    {"satcatid": "first"},
    {"satname": "first"},
    {"owner": "most_common"},
    {"launchvehicle": "most_common"},
    {"purpose": ["Communications"]},
    {"year": [2000, 2010]},
    {"status": ["Active"], "orbit": ["GEO"], "owner": "most_common", "year": [2000, 2026]},
], ids=lambda c: ",".join(c) or "everything")
def test_filter_returns_exact_set(sample_df, filters, t_ref, case):
    first = sample_df.iloc[0]
    resolve = {
        "satcatid": lambda v: str(first.SatCatId),
        "satname": lambda v: first.ObjectName,
        "owner": lambda v: [sample_df.Owner.value_counts().index[0]],
        "launchvehicle": lambda v: [sample_df.LaunchVehicleClass.value_counts().index[0]],
    }
    kw = {k: resolve[k](v) if v in ("first", "most_common") else v for k, v in case.items()}
    out, _, encoded, args = run(sample_df, filters, **kw)
    assert set(out.SatCatId) == expected_ids(sample_df, t_ref, **args)
    assert len(out) == out.SatCatId.nunique()
    np.testing.assert_array_equal(encoded, (out["Status"] == "Active").astype(int).to_numpy())
    assert out[["x", "y", "z", "lat", "lon", "alt", "xp", "yp", "zp"]].notna().all().all()


def test_filters_do_not_modify_the_shared_catalogue(sample_df, filters):
    """Callbacks pass the app's one in-memory catalogue; filtering must not change it."""
    df = sample_df.copy()
    before = df.copy()
    filter_satellite_data(df, filters[1], ALL_STATUS, ALL_ORBITS, None, None, [], [], [],
                          list(filters[0]["launchyear"]))
    assert df.equals(before)


@pytest.mark.parametrize("column", ["LaunchMass", "Bstar", "ObjectId"])
def test_blank_non_position_field_does_not_hide_a_satellite(sample_df, filters, t_ref, column):
    """Only a satellite SGP4 cannot place is dropped; a blank descriptive or OMM field does not hide one."""
    df = sample_df.copy()
    df.loc[0, column] = np.nan
    out, _, _, _ = run(df, filters)
    assert df.loc[0, "SatCatId"] in set(out.SatCatId)


def test_orbital_path_skips_points_after_decay(sample_df, filters, t_ref):
    """Copilot review on #56: a satellite that propagates now but decays within its plotted period keeps its valid
    points; the failed ones are dropped (with their times) instead of reaching the 2D hover labels as NaN, which
    raised in .astype(int). Elements: 16.3 rev/day with B* 0.05 decay ~28 min after epoch (sgp4 error 6)."""
    from app.helper.helper__plot_display import create_2d_scatter_hover_label
    one = sample_df[(sample_df.OrbitClass == "LEO") & (sample_df.Eccentricity < 0.01)].iloc[[0]].copy()
    one["MeanMotion"], one["Bstar"], one["Epoch"] = 16.3, 0.05, t_ref.strftime("%Y-%m-%dT%H:%M:%S.%f")
    path = generate_orbital_path(one, 360, t_ref, False)
    assert 0 < len(path) < 360
    assert not path[["lat", "lon", "alt"]].isna().any().any()
    assert path["Datetime"].iloc[0] == t_ref
    assert len(create_2d_scatter_hover_label(path)[0]) == len(path)


@pytest.mark.parametrize("eci", [True, False], ids=["3d-orbit", "2d-ground-track"])
def test_orbital_path(sample_df, filters, t_ref, eci):
    """One orbital period, `res` points from now; each point is the satellite's position at its own time
    (2D ground track) or, for the 3D orbit drawing, the inertial path whose first point is the satellite now."""
    sat = sample_df[(sample_df.OrbitClass == "LEO") & (sample_df.Eccentricity < 0.01)].iloc[0]
    one, _, _, _ = run(sample_df, filters, satcatid=str(sat.SatCatId))
    res = 60
    path = generate_orbital_path(one, res, t_ref, eci)
    assert len(path) == res
    assert (path["SatCatId"] == sat.SatCatId).all()
    assert path["Datetime"].iloc[0] == t_ref
    span = (path["Datetime"].iloc[-1] - t_ref).total_seconds()
    assert span == pytest.approx(sat.OrbitalPeriod * 60, abs=1)
    now = compute_satloc(satrecs_for(one), t_ref, EARTH_RADIUS_KM, False)[0]
    np.testing.assert_allclose(path[["x", "y", "z"]].iloc[0], now[:3], atol=1e-6)
    np.testing.assert_allclose(path[["lat", "alt"]].iloc[0], now[[3, 5]], atol=1e-6)
    # After one period the satellite is back where it started in inertial space (within 1% of the radius)
    start, end = path[["x", "y", "z"]].iloc[0].to_numpy(), path[["x", "y", "z"]].iloc[-1].to_numpy()
    assert np.linalg.norm(end - start) < 0.01 * np.linalg.norm(start)
