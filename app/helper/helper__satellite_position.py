#!/usr/bin/env python

"""

This module contains functions used to calculate satellite position:
- Convert coordinates from the TEME version of the Earth Centred Coordinate System to geodetic (WGS 84) latitude,
  longitude and altitude, the convention of maps and other trackers.
- Calculate Earth geometry in Cartesian coordinates and satellite position from each satellite's element set
  (OMM fields; TLE lines as a fallback for one release, plan 1.3).

Based on: https://gist.github.com/tomaszmrugalski/4bc1dbac915def55596cc9fb785fe7bf

Example:

        $ python helper__satellite_position.py

Functions:
    - julianDateToGMST2: Converts Julian date to GMST (Greenwich Mean Sidereal Time 1982 )
    - longitude_trunc: Truncate longitude to range [-pi,+pi]
    - teme2geodetic: Convert ECI (Earth Centred Inertial) coordinates to WGS 84 latitude, longitude and altitude
    - satrecs_for: One sgp4 Satrec per catalogue row, built once per element set and reused
    - compute_satloc: Compute Geodetic position of satellites from their Satrecs and UTC datetime
    - lla_to_xyz: Convert geodetic position to Cartesian coordinates
    - sphere: Compute surface of Earth as a sphere in Cartesian coordinates

"""

import numpy as np
import pandas as pd
from math import pi
from sgp4 import omm
from sgp4.api import Satrec, SatrecArray, jday

# OMM keyword (what sgp4.omm.initialize reads) -> satcat_tle.csv column
OMM_FIELDS = {
    "EPOCH": "Epoch", "MEAN_MOTION": "MeanMotion", "ECCENTRICITY": "Eccentricity", "INCLINATION": "Inclination",
    "RA_OF_ASC_NODE": "RaOfAscNode", "ARG_OF_PERICENTER": "ArgOfPericenter", "MEAN_ANOMALY": "MeanAnomaly",
    "BSTAR": "Bstar", "MEAN_MOTION_DOT": "MeanMotionDot", "MEAN_MOTION_DDOT": "MeanMotionDdot",
    "REV_AT_EPOCH": "RevAtEpoch", "ELEMENT_SET_NO": "ElementSetNo", "EPHEMERIS_TYPE": "EphemerisType",
    "CLASSIFICATION_TYPE": "ClassificationType", "OBJECT_ID": "ObjectId", "NORAD_CAT_ID": "SatCatId",
}
# The same element set in the objects dataset (D-009, D-010): the warehouse's names, which are the OMM keywords in lower
# case, with the catalogue number as satcat_id.
OMM_FIELDS_OBJECTS = {k: ("satcat_id" if k == "NORAD_CAT_ID" else k.lower()) for k in OMM_FIELDS}

# Building a Satrec costs ~15x more than propagating it, so each element set is built once per process and reused
# by every callback. Key: the catalogue number plus every value the Satrec is built from (all OMM fields, or both TLE
# lines), so any revised element set, even one republished with the same epoch, gets a new Satrec. ~1 kB each;
# cleared if it outgrows several catalogues' worth.
_satrec_cache = {}
_SATREC_CACHE_MAX = 100_000

# sgp4 (2.27) refuses catalogue numbers above 339,999 (the largest Alpha-5 can write). The number is only a label in
# the Satrec and never enters the orbit calculation, so a larger one is built with 0; the app keeps the real
# SatCatId in its own columns.
_SGP4_MAX_SATNUM = 339_999


def _complete(df, cols):
    """Boolean array: rows with a value in every one of `cols` (False if a column is missing)."""
    if not all(c in df.columns for c in cols):
        return np.zeros(len(df), dtype=bool)
    return df[list(cols)].notna().all(axis=1).to_numpy()


def _sources(df, fields=OMM_FIELDS):
    """Per row: 'omm' (all OMM columns present), 'tle' (else both TLE lines) or 'none'."""
    use_omm = _complete(df, fields.values())
    use_tle = ~use_omm & _complete(df, ("TLE1", "TLE2"))
    return np.where(use_omm, "omm", np.where(use_tle, "tle", "none"))


def _build_satrec(row, source, names=OMM_FIELDS):
    """A Satrec from the OMM columns ('omm') or TLE1/TLE2 ('tle': fallback kept for one release, for a pre-OMM
    satcat_tle.csv); None for 'none' (no position)."""
    if source == "omm":
        fields = {k: row[c] for k, c in names.items()}
        if int(fields["NORAD_CAT_ID"]) > _SGP4_MAX_SATNUM:
            fields["NORAD_CAT_ID"] = 0
        sat = Satrec()
        omm.initialize(sat, fields)
        return sat
    if source == "tle":
        return Satrec.twoline2rv(row["TLE1"], row["TLE2"])
    return None


def satrecs_for(df, fields=OMM_FIELDS):
    """
    One sgp4 Satrec per row of a satcat_tle.csv frame (or, with fields=OMM_FIELDS_OBJECTS, of the objects dataset),
    in row order (None for a row without an element set). Built once per element set (see _satrec_cache), so
    callbacks only propagate.

    @param df: (DataFrame) catalogue rows: the catalogue number plus the OMM columns and/or TLE1, TLE2
    @param fields: (dict) OMM keyword -> column name
    @return: list of Satrec or None, one per row
    """
    sources = _sources(df, fields)
    n = len(df)

    def values(cols):   # one tuple per row of the given columns (all None if a column is absent)
        if all(c in df.columns for c in cols):
            return list(zip(*(df[c].to_numpy() for c in cols)))
        return [None] * n

    omm_values = values(list(fields.values()))
    tle_values = values(["TLE1", "TLE2"])
    keys = [(i, src, o if src == "omm" else t if src == "tle" else None)
            for i, src, o, t in zip(df[fields["NORAD_CAT_ID"]].to_numpy(), sources, omm_values, tle_values)]
    missing = [n for n, k in enumerate(keys) if k not in _satrec_cache]
    if missing:
        if len(_satrec_cache) + len(missing) > _SATREC_CACHE_MAX:
            _satrec_cache.clear()
            missing = list(range(len(keys)))
        cols = [c for c in dict.fromkeys(list(fields.values()) + ["TLE1", "TLE2"]) if c in df.columns]
        rows = df.iloc[missing][cols].to_dict("records")
        for n, row in zip(missing, rows):
            _satrec_cache[keys[n]] = _build_satrec(row, sources[n], fields)
    return [_satrec_cache[k] for k in keys]


def satrec_sources(df, fields=OMM_FIELDS):
    """Counts of rows whose Satrec comes from OMM, from the TLE fallback, or neither (for the start-up log)."""
    sources = _sources(df, fields)
    return {s: int((sources == s).sum()) for s in ("omm", "tle", "none")}


def julianDateToGMST2(jd, fr):
    """
    Converts Julian date (expressed at two floats) to GMST (Greenwich Mean Sidereal Time 1982).
    Parameters:
    jd : float - Julian date full integer + 0.5
    fr : float - fractional part of the Julian date
    Returns
    =======
    A single floating point representing a GMST, expressed in radians
    This calculation takes into consideration the precession, but not nutation.
    Source: https://github.com/skyfielders/python-skyfield/blob/master/skyfield/sgp4lib.py
    - theta_GSMT1982 function
    This angle defines the difference between the idiosyncratic True
    Equator Mean Equinox (TEME) frame of reference used by SGP4 and the
    more standard Pseudo Earth Fixed (PEF) frame of reference.
    From AIAA 2006-6753 Appendix C.
    """
    tau = 6.283185307179586476925287

    _second = 1.0 / (24.0 * 60.0 * 60.0)

    T0 = 2451545.0  # J2000, 2000-Jan-01 12h UT1 as Julian date

    # First calculate number of days since J2000 (2000-Jan-01 12h UT1)
    d = jd - T0
    d = d + fr

    # Now convert this to centuries. Don't ask me why.
    t = d / 36525.0

    # Don't undersran
    g = 67310.54841 + (8640184.812866 + (0.093104 + (-6.2e-6) * t) * t) * t
    dg = 8640184.812866 + (0.093104 * 2.0 + (-6.2e-6 * 3.0) * t) * t
    theta = ((jd + fr) % 1.0 + g * _second % 1.0) * tau
    theta_dot = (1.0 + dg * _second / 36525.0) * tau
    return theta, theta_dot


def longitude_trunc(lon):
    """ Wrap a longitude (radians) into [-pi, pi). The GMST subtracted before this can be up to 4*pi, so a single
    +/-2*pi step was not enough: hover labels and the table showed values down to -405 deg. """
    return (lon + pi) % (2 * pi) - pi


# WGS 84 ellipsoid (NGA.STND.0036, "World Geodetic System 1984"): semi-major axis and flattening
WGS84_A_KM = 6378.137
WGS84_F = 1 / 298.257223563
_WGS84_E2 = WGS84_F * (2 - WGS84_F)   # first eccentricity squared


def geodetic_from_cartesian(x, y, z):
    """
    Geodetic latitude (rad) and height above the WGS 84 ellipsoid (km) of Earth-fixed coordinates (km), by the
    iterative method in T.S. Kelso, "Orbital Coordinate Systems, Part III" (https://celestrak.org/columns/v02n03/).
    Vectorised; five iterations converge to well under a millimetre for any orbit.
    """
    r = np.sqrt(x * x + y * y)
    lat = np.arctan2(z, r)
    for _ in range(5):
        c = 1 / np.sqrt(1 - _WGS84_E2 * np.sin(lat) ** 2)
        lat = np.arctan2(z + WGS84_A_KM * c * _WGS84_E2 * np.sin(lat), r)
    c = 1 / np.sqrt(1 - _WGS84_E2 * np.sin(lat) ** 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        # height from r / cos(lat) - aC; near the poles (cos(lat) ~ 0) use z / sin(lat) - aC(1 - e2) instead
        alt = np.where(np.abs(np.cos(lat)) > 1e-6,
                       r / np.cos(lat) - WGS84_A_KM * c,
                       z / np.sin(lat) - WGS84_A_KM * c * (1 - _WGS84_E2))
    return lat, alt


def teme2geodetic(x, y, z, t, re=None):
    """
    Converts ECI coords (x,y,z - expressed in km) to LLA (latitude, longitude, altitude) on the WGS 84 ellipsoid:
    geodetic latitude and height above the ellipsoid, as on maps and other trackers. (Until plan 1.3 this assumed a
    spherical Earth: geocentric latitude and height above a 6378.137 km sphere, up to 0.19 deg and ~21 km off.)
    Longitude: the TEME frame turned by GMST, as in T.S. Kelso's "Orbital Coordinate Systems, Part III"
    https://celestrak.org/columns/v02n03/.
    Parameters
    ==========
    x,y,z : floating point or vector - coordates in TEME (True Equator Mean Equinoex) version of ECI (Earth Centered Intertial) coords system.
            This is the system that's produced by SGP4 models.
    t : datetime object or vector of datetime objects in UTC timezone. If vector, must be same length as x,y,z
    re : unused (kept for callers of the old spherical version)
    """

    if isinstance(t, (np.ndarray, list)):
        if len(x) != len(t) or len(x) != len(t) or len(x) != len(t):
            print("If t is a vector, must be the same shape as x,y,z")
            return
        dt_array = np.array([(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) for dt in t])
        jd, fr = jday(dt_array[:, 0], dt_array[:, 1], dt_array[:, 2],
                      dt_array[:, 3], dt_array[:, 4], dt_array[:, 5])
    else:
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)

    gmst = julianDateToGMST2(jd, fr)[0]

    lat, alt = geodetic_from_cartesian(x, y, z)   # z is unchanged by the rotation about the pole, r likewise
    lon = np.arctan2(y, x) - gmst  # lambda-E
    lon = longitude_trunc(lon)

    return lat * 180 / np.pi, lon * 180 / np.pi, alt


teme2geodetic_spherical = teme2geodetic   # old name


def compute_satloc(satrecs, time_in, re, eci):
    '''
    Compute satellite positions with the Simplified General Perturbations (SGP4) propagator, in the TEME version of
    the Earth Centred Coordinate System, then geodetic latitude/longitude/altitude on the WGS 84 ellipsoid.

    @param satrecs: list of N Satrec (or None: that row is all-NaN) for one time, or one Satrec for a list of times
                    (see satrecs_for)
    @param time_in: (datetime) UTC datetime as datetime object or list of datetime objects
    @param re: (float) unused since plan 1.3 (WGS 84 is built in); kept for existing callers
    @param eci: (boolean) set True to compute geodetic position for fixed datetime
    @return: N x 6 floating point array - contains x, y, z in ECI, and latitude, longitude and alitutde
    '''
    # Define time used to compute Geodetic position
    time_in2 = time_in

    # Calculate Julian date
    if isinstance(time_in, (np.ndarray, list)):
        if eci: time_in2 = time_in[0]
        if not isinstance(satrecs, Satrec):
            raise ValueError("A list of times needs a single Satrec (one satellite)")
        else:
            dt_array = np.array([(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) for dt in time_in])
            jd, fr = jday(dt_array[:, 0], dt_array[:, 1], dt_array[:, 2],
                          dt_array[:, 3], dt_array[:, 4], dt_array[:, 5])
    else:
        jd, fr = jday(time_in.year, time_in.month, time_in.day, time_in.hour, time_in.minute, time_in.second)
        jd = np.reshape(np.array(jd), (1,))
        fr = np.reshape(np.array(fr), (1,))

    # Compute TEME - xyz Satellite position
    if isinstance(time_in, (np.ndarray, list)):
        # one satellite, many times: one Satrec, propagated to all times at once
        err, teme_p2, _ = satrecs.sgp4_array(np.asarray(jd, dtype=float), np.asarray(fr, dtype=float))
        teme_p2[err != 0] = np.nan
    else:
        # many satellites, one time; rows without a Satrec stay NaN
        teme_p2 = np.full((len(satrecs), 3), np.nan)
        valid = [i for i, s in enumerate(satrecs) if s is not None]
        if valid:
            err, teme_p, _ = SatrecArray([satrecs[i] for i in valid]).sgp4(jd, fr)
            teme_p = teme_p[:, 0, :]
            teme_p[err[:, 0] != 0] = np.nan
            teme_p2[valid] = teme_p

    # Convert TEME to geodetic latitude, longitude and altitude (WGS 84)
    lat, lon, alt = teme2geodetic(teme_p2[:, 0], teme_p2[:, 1], teme_p2[:, 2], time_in2)

    return np.concatenate((teme_p2, np.vstack((lat, lon, alt)).T), axis=1)


def lla_to_xyz(lat, lon, alt, re):
    '''
    Compute satellite position in Cartesian geometry (x,y,z) using Longitude, Latitude and Altitude

    @param lat: (array) floating point vector containing list of latitudes
    @param lon: (array) floating point vector containing list of longitudes
    @param alt: (array) floating point vector containing list of altitudes
    @return: x0, y0, z0 (array) floating point vectors containing list of x, y and z positions respectively
    '''

    re = alt + re
    lon = lon + 180
    # Set up coordinates for points on the sphere
    x0 = re * np.cos(lat * np.pi / 180) * np.cos(lon * np.pi / 180)
    y0 = re * np.cos(lat * np.pi / 180) * np.sin(lon * np.pi / 180)
    z0 = re * np.sin(lat * np.pi / 180)

    # Set up trace
    return x0, y0, z0


def sphere(size, texture):
    '''
    Compute location of Earth surface in Cartesian coordinates assuming Spherical Earth

    @param size: (float) single floating point array of Earth radius
    @param texture: (array) floating point array of two-dimensional Earth image
    @return: x0, y0, z0 (array) floating point array of x, y and z position of Earth surface
    '''

    N_lon = int(texture.shape[0])
    N_lat = int(texture.shape[1])
    lon = np.linspace(0, 2 * np.pi, N_lon)
    lat = np.linspace(0, np.pi, N_lat)

    # Set up coordinates for points on the sphere
    x0 = size * np.outer(np.cos(lon), np.sin(lat))
    y0 = size * np.outer(np.sin(lon), np.sin(lat))
    z0 = size * np.outer(np.ones(N_lon), np.cos(lat))

    # Set up trace
    return x0, y0, z0