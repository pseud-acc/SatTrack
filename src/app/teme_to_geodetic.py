#!/usr/bin/env python

"""

This module contains functions used to convert coordinates from the TEME version of the Earth Centred Coordinate System to
Latitude, Longitude and Altitude.

Based on: https://gist.github.com/tomaszmrugalski/4bc1dbac915def55596cc9fb785fe7bf

Example:

        $ python teme_to_geodetic.py

Functions:
    - julianDateToGMST2 - Converts Julian date to GMST (Greenwich Mean Sidereal Time 1982 )
    - longitude_trunc - truncate longitude to range [-pi,+pi]
    - teme2geodetic_spherical - convert ECI (Earth Centred Inertial) coordinates to Longitude, Latitude and Altitude
Todo:
    * 

"""

from sgp4.api import jday
from math import atan, atan2, sqrt, pi, sin, cos, asin, acos, tan
import numpy as np



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

    T0 = 2451545.0 # J2000, 2000-Jan-01 12h UT1 as Julian date

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
    lon = lon - 2*pi*np.sign(lon)*(abs(lon) > pi)**2
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

    if isinstance(t, (np.ndarray,list)):
        if len(x) != len(t) or len(x) != len(t) or len(x) != len(t):
            print("If t is a vector, must be the same shape as x,y,z")
            return
        dt_array = np.array([(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) for dt in t])
        jd, fr = jday(dt_array[:,0], dt_array[:,1], dt_array[:,2], 
                      dt_array[:,3], dt_array[:,4], dt_array[:,5])
    else:
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)
    
    gmst = julianDateToGMST2(jd, fr)[0]

    lat = np.arctan2(z, np.sqrt(x*x + y*y)) # phi
    lon = np.arctan2(y, x) - gmst # lambda-E
    lon = longitude_trunc(lon)
    alt = np.sqrt(x*x + y*y + z*z) - re # h

    return lat*180/np.pi, lon*180/np.pi, alt