-- Tracking unit: one row per on-orbit object in the Space-Track GP feed, with the derived orbit class.
-- orbit_class uses the live app's 5-class rule (decided 2026-10-25); GCAT OpOrbit stays a separate detail.
with cte_stg__spacetrack__gp as (
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
        , _loaded_at
    from {{ ref('stg__spacetrack__gp') }}
)

, cte_final as (
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
        , {{ helper__classify_orbit_class('orbital_period', 'eccentricity', 'mean_motion', 'inclination') }} as orbit_class
        , date_diff('second', epoch, _loaded_at) / 86400.0 as tle_age_days
        , _loaded_at
        , {{ helper__audit_fields() }}
    from cte_stg__spacetrack__gp
)

select * from cte_final
