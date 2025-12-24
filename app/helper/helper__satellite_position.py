#!/usr/bin/env python

"""

This module contains functions used to calculate satellite position:
- Convert coordinates from the TEME version of the Earth Centred Coordinate System to Latitude, Longitude and Altitude.
- Calculate Earth geometry in Cartesian coordinates and satellite position using Two-Line Element data.

Based on: https://gist.github.com/tomaszmrugalski/4bc1dbac915def55596cc9fb785fe7bf

Example:

        $ python helper__satellite_position.py

Functions:
    - julianDateToGMST2: Converts Julian date to GMST (Greenwich Mean Sidereal Time 1982 )
    - longitude_trunc: Truncate longitude to range [-pi,+pi]
    - teme2geodetic_spherical: Convert ECI (Earth Centred Inertial) coordinates to Longitude, Latitude and Altitude
    - compute_satloc: Compute Geodetic position of satellite from TLE data and UTC datetime
    - lla_to_xyz: Convert geodetic position to Cartesian coordinates
    - sphere: Compute surface of Earth as a sphere in Cartesian coordinates

"""

import numpy as np
from math import pi
from sgp4.api import Satrec, SatrecArray, jday

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
    """ Makes sure the longitude is within -2*pi ... 2*pi range """
    lon = lon - 2 * pi * np.sign(lon) * (abs(lon) > pi) ** 2
    return lon


def teme2geodetic_spherical(x, y, z, t, re):
    """
    Converts ECI coords (x,y,z - expressed in km) to LLA (longitude, lattitude, altitude).
    This function assumes the Earth is completely round.
    The calculations here are based on T.S. Kelso's excellent paper "Orbital Coordinate Systems, Part III
    https://celestrak.com/columns/v02n03/.
    Parameters
    ==========
    x,y,z : floating point or vector - coordates in TEME (True Equator Mean Equinoex) version of ECI (Earth Centered Intertial) coords system.
            This is the system that's produced by SGP4 models.
    t : datetime object or vector of datetime objects in UTC timezone. If vector, must be same length as x,y,z
    re : floating point - Earth radius.
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

    lat = np.arctan2(z, np.sqrt(x * x + y * y))  # phi
    lon = np.arctan2(y, x) - gmst  # lambda-E
    lon = longitude_trunc(lon)
    alt = np.sqrt(x * x + y * y + z * z) - re  # h

    return lat * 180 / np.pi, lon * 180 / np.pi, alt


def compute_satloc(tle_in, time_in, re, eci):
    '''
    Compute satellite position from Two-Line Element (TLE) data. TLEs are passed through a Simplified General Perturbations (SGP4) propagator to calculate satellite position in the TEME version of the Earth Centred Coordinate System assuming a spherical Earth.

    @param tle_in: (dataframe) N x 2 floating point array - contains TLE1 and TLE2 data in the respective columns
    @param time_in: (datetime) UTC datetime as datetime object or list of datetime objects
    @param re: (float) single floating point of Earth radius
    @param eci: (boolean) set True to compute geodetic position for fixed datetime
    @return: N x 6 floating point array - contains x, y, z in ECI, and latitude, longitude and alitutde
    '''
    # Define time used to compute Geodetic position
    time_in2 = time_in

    # Calculate Julian date
    if isinstance(time_in, (np.ndarray, list)):
        if eci: time_in2 = time_in[0]
        if tle_in.shape[0] > 2:
            raise ValueError("Both TLE and datetime arguments cannot be arrays")
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
        teme_p = []
        for j, f in zip(jd, fr):
            teme_p.append([Satrec.twoline2rv(tle_in[0], tle_in[1]).sgp4(j, f)[1]])
        teme_p2 = np.array(teme_p)[:, 0]
    else:
        # Create array of sqgp4 satellite objects
        satellite_list = list()
        for t in tle_in:
            satellite_list.append(Satrec.twoline2rv(t[0], t[1]))
        satellite_array = SatrecArray(satellite_list)
        _, teme_p, _ = satellite_array.sgp4(jd, fr)
        teme_p2 = np.reshape(teme_p, (teme_p.shape[0], teme_p.shape[2]))

    # Convert TEME to Geodetic - assume spherical Earth
    lat, lon, alt = teme2geodetic_spherical(teme_p2[:, 0], teme_p2[:, 1], teme_p2[:, 2], time_in2, re)

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