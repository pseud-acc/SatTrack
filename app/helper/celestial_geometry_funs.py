#!/usr/bin/env python

"""

This module contains functions used to calculate Earth geometry in Cartesian coordinates and satellite position using Two-Line Element data.

Example:

        $ python celestial_geometry_funs.py

Functions:
    compute_satloc: Compute Geodetic position of satellite from TLE data and UTC datetime
    lla_to_xyz: Convert geodetic position to Cartesian coordinates
    sphere: Compute surface of Earth as a sphere in Cartesian coordinates

Todo:
    * 

"""

# Packages
import sys

import numpy as np
from sgp4.api import Satrec, SatrecArray
from sgp4.api import jday

sys.path.append("../../")
from app.helper.teme_to_geodetic import teme2geodetic_spherical

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
    
    #Calculate Julian date
    if isinstance(time_in, (np.ndarray,list)):
        if eci: time_in2 = time_in[0]
        if tle_in.shape[0] > 2:
            raise ValueError("Both TLE and datetime arguments cannot be arrays")
        else:
            dt_array = np.array([(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) for dt in time_in])
            jd, fr = jday(dt_array[:,0], dt_array[:,1], dt_array[:,2], 
                          dt_array[:,3], dt_array[:,4], dt_array[:,5])
    else:
        jd, fr = jday(time_in.year,time_in.month,time_in.day,time_in.hour,time_in.minute,time_in.second)
        jd = np.reshape(np.array(jd),(1,))
        fr = np.reshape(np.array(fr),(1,))
    

    #Compute TEME - xyz Satellite position
    if isinstance(time_in, (np.ndarray,list)):
        teme_p = []
        for j,f in zip(jd,fr):
            teme_p.append([Satrec.twoline2rv(tle_in[0], tle_in[1]).sgp4(j,f)[1]])
        teme_p2 = np.array(teme_p)[:,0]
    else:
        #Create array of sqgp4 satellite objects
        satellite_list = list()
        for t in tle_in:
            satellite_list.append(Satrec.twoline2rv(t[0],t[1]))
        satellite_array = SatrecArray(satellite_list)        
        _, teme_p, _ = satellite_array.sgp4(jd, fr)
        teme_p2 = np.reshape(teme_p,(teme_p.shape[0],teme_p.shape[2]))

    #Convert TEME to Geodetic - assume spherical Earth
    lat, lon, alt = teme2geodetic_spherical(teme_p2[:,0],teme_p2[:,1],teme_p2[:,2], time_in2, re)
    
    return np.concatenate((teme_p2,np.vstack((lat,lon,alt)).T), axis=1)

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
    x0 = re * np.cos(lat*np.pi/180) * np.cos(lon*np.pi/180)
    y0 = re * np.cos(lat*np.pi/180) * np.sin(lon*np.pi/180)
    z0 = re * np.sin(lat*np.pi/180)
    
    # Set up trace
    return x0,y0,z0

def sphere(size, texture):
    
    ''' 
    Compute location of Earth surface in Cartesian coordinates assuming Spherical Earth

    @param size: (float) single floating point array of Earth radius
    @param texture: (array) floating point array of two-dimensional Earth image
    @return: x0, y0, z0 (array) floating point array of x, y and z position of Earth surface
    '''          
    
    N_lon = int(texture.shape[0])
    N_lat = int(texture.shape[1])
    lon = np.linspace(0,2*np.pi,N_lon)
    lat = np.linspace(0,np.pi,N_lat)
    
    # Set up coordinates for points on the sphere
    x0 = size * np.outer(np.cos(lon),np.sin(lat))
    y0 = size * np.outer(np.sin(lon),np.sin(lat))
    z0 = size * np.outer(np.ones(N_lon),np.cos(lat))
    
    # Set up trace
    return x0,y0,z0
