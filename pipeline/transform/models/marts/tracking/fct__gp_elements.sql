-- One row per on-orbit object in the Space-Track GP feed: orbital elements, TLE lines and the derived orbit class. The app's tracking table.
with cte_int__spacetrack__satellite_catalogue as (
    select
        satcat_id
        , object_name
        , object_id
        , object_type
        , country_code
        , launch_date
        , launch_site
        , epoch
        , mean_motion
        , eccentricity
        , inclination
        , ra_of_asc_node
        , arg_of_pericenter
        , mean_anomaly
        , bstar
        , semimajor_axis
        , orbital_period
        , apoapsis
        , periapsis
        , rcs_size
        , tle_line_1
        , tle_line_2
        , orbit_class
        , tle_age_days
        , _loaded_at
    from {{ ref('int__spacetrack__satellite_catalogue') }}
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(object_name as varchar) as object_name
        , cast(object_id as varchar) as object_id
        , cast(object_type as varchar) as object_type
        , cast(country_code as varchar) as country_code
        , cast(launch_date as date) as launch_date
        , cast(launch_site as varchar) as launch_site
        , cast(epoch as timestamp) as epoch
        , cast(mean_motion as double) as mean_motion
        , cast(eccentricity as double) as eccentricity
        , cast(inclination as double) as inclination
        , cast(ra_of_asc_node as double) as ra_of_asc_node
        , cast(arg_of_pericenter as double) as arg_of_pericenter
        , cast(mean_anomaly as double) as mean_anomaly
        , cast(bstar as double) as bstar
        , cast(semimajor_axis as double) as semimajor_axis
        , cast(orbital_period as double) as orbital_period
        , cast(apoapsis as double) as apoapsis
        , cast(periapsis as double) as periapsis
        , cast(rcs_size as varchar) as rcs_size
        , cast(tle_line_1 as varchar) as tle_line_1
        , cast(tle_line_2 as varchar) as tle_line_2
        , cast(orbit_class as varchar) as orbit_class
        , cast(tle_age_days as double) as tle_age_days
        , cast(_loaded_at as timestamp) as _loaded_at
        , {{ helper__audit_fields() }}
    from cte_int__spacetrack__satellite_catalogue
)

select * from cte_final
