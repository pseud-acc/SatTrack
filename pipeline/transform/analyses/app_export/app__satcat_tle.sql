-- App export: satcat_tle.csv, the satellite file the live SatTrack Dash app loads (S3 app/satcat_tle.csv, read with
-- a plain pandas.read_csv, no dtypes or parse_dates; app/core/state.py).
-- Columns, order and value formats follow the legacy pipeline's export (removed in 2.2.0), less StatusCode, UcsData
-- and OrbitClassEstimated: the app never read them and this pipeline has no source for them.
-- Descriptive gaps are filled ('Unknown' for text, -1.0 for numbers, as in the old file) so the file stays complete.
-- TLE1/TLE2 may be empty: the app propagates from the OMM elements (plan 1.3) and keeps the TLE lines only as a
-- fallback for a pre-OMM file, so a satellite without TLE lines (e.g. above 339,999, beyond Alpha-5) is still shown.
-- Scope matches the old app: Earth-orbiting payloads with a full element set and a positive period.
-- Elements: the OMM fields Space-Track publishes (CCSDS OMM keywords, after the TLE columns), so the app can build its
-- propagator from them with sgp4.omm.initialize (plan 1.3). Numbers are copied, not rounded or parsed from TLE text;
-- Epoch is written as %Y-%m-%dT%H:%M:%S.%f, the format sgp4.omm.initialize reads.
-- Two sources, so positions never wait for the GCAT details: what each satellite is (name, owner, status, purpose)
-- comes from fct__satellite_master (enrichment unit), and where it is (element set, TLE lines, period) from
-- fct__gp_elements (tracking unit). When enrichment is held, positions still update every run; a satellite new to
-- the GP feed appears once enrichment next succeeds, and one that left it disappears at once.
with cte_fct__satellite_master as (
    select
        satcat_id
        , object_name
        , object_type
        , flag_in_orbit
        , operational_status
        , launch_year
        , owner_country
        , site_location_country
        , ownership_class_labels
        , mission_category_labels
        , launch_vehicle_brand
        , orbit_class
        , mass_kg
    from {{ ref('fct__satellite_master') }}
)

, cte_fct__gp_elements as (
    select
        satcat_id
        , object_id
        , epoch
        , mean_motion
        , eccentricity
        , inclination
        , ra_of_asc_node
        , arg_of_pericenter
        , mean_anomaly
        , bstar
        , mean_motion_dot
        , mean_motion_ddot
        , rev_at_epoch
        , element_set_no
        , ephemeris_type
        , classification_type
        , orbital_period
        , tle_line_1
        , tle_line_2
    from {{ ref('fct__gp_elements') }}
)

, cte_app_scope as (
    select
        sat.satcat_id
        , object_name
        , operational_status
        , launch_year
        , owner_country
        , site_location_country
        , ownership_class_labels
        , mission_category_labels
        , launch_vehicle_brand
        , orbit_class
        , round(gp.orbital_period, 2) as orbital_period
        , mass_kg
        , gp.object_id
        , gp.epoch
        , gp.mean_motion
        , gp.eccentricity
        , gp.inclination
        , gp.ra_of_asc_node
        , gp.arg_of_pericenter
        , gp.mean_anomaly
        , gp.bstar
        , gp.mean_motion_dot
        , gp.mean_motion_ddot
        , gp.rev_at_epoch
        , gp.element_set_no
        , gp.ephemeris_type
        , gp.classification_type
        , gp.tle_line_1
        , gp.tle_line_2
    from cte_fct__satellite_master as sat
    inner join cte_fct__gp_elements as gp
        on sat.satcat_id = gp.satcat_id
    where sat.object_type = 'PAYLOAD'
        and sat.flag_in_orbit = 1
        -- a full element set: every field sgp4.omm.initialize reads
        and gp.object_id is not null
        and gp.epoch is not null
        and gp.mean_motion is not null
        and gp.eccentricity is not null
        and gp.inclination is not null
        and gp.ra_of_asc_node is not null
        and gp.arg_of_pericenter is not null
        and gp.mean_anomaly is not null
        and gp.bstar is not null
        and gp.mean_motion_dot is not null
        and gp.mean_motion_ddot is not null
        and gp.rev_at_epoch is not null
        and gp.element_set_no is not null
        and gp.ephemeris_type is not null
        and gp.classification_type is not null
        and gp.orbital_period > 0
        and sat.launch_year is not null
)

, cte_app_columns as (
    select
        satcat_id
        , coalesce(object_name, 'Unknown') as object_name
        , launch_year
        , orbital_period
        , coalesce(mass_kg, -1.0) as launch_mass
        , inclination
        , coalesce(operational_status, 'Inactive') as operational_status
        , coalesce(site_location_country, 'Unknown') as launch_site_country
        , coalesce(owner_country, 'Unknown') as owner
        -- labels sorted and joined with '/', as the old pipeline standardised UCS Users
        , coalesce(nullif(array_to_string(list_sort(ownership_class_labels), '/'), ''), 'Unknown') as use_type
        -- joined with '/': the app splits Purpose on '/' to build its multi-select filter
        , coalesce(nullif(array_to_string(mission_category_labels, '/'), ''), 'Unknown') as purpose
        , coalesce(launch_vehicle_brand, 'Unknown') as launch_vehicle_class
        , tle_line_1
        , tle_line_2
        , mean_motion
        , eccentricity
        , orbit_class
        , strftime(epoch, '%Y-%m-%dT%H:%M:%S.%f') as epoch_text
        , ra_of_asc_node
        , arg_of_pericenter
        , mean_anomaly
        , bstar
        , mean_motion_dot
        , mean_motion_ddot
        , rev_at_epoch
        , element_set_no
        , ephemeris_type
        , classification_type
        , object_id
    from cte_app_scope
)

, cte_final as (
    select
        cast(satcat_id as bigint) as "SatCatId"
        , cast(object_name as varchar) as "ObjectName"
        , cast(launch_year as bigint) as "LaunchYear"
        , cast(orbital_period as double) as "OrbitalPeriod"
        , cast(launch_mass as double) as "LaunchMass"
        , cast(inclination as double) as "Inclination"
        , cast(operational_status as varchar) as "Status"
        , cast(launch_site_country as varchar) as "LaunchSiteCountry"
        , cast(owner as varchar) as "Owner"
        , cast(use_type as varchar) as "UseType"
        , cast(purpose as varchar) as "Purpose"
        , cast(launch_vehicle_class as varchar) as "LaunchVehicleClass"
        , cast(tle_line_1 as varchar) as "TLE1"
        , cast(tle_line_2 as varchar) as "TLE2"
        , cast(mean_motion as double) as "MeanMotion"
        , cast(eccentricity as double) as "Eccentricity"
        , cast(orbit_class as varchar) as "OrbitClass"
        , cast(epoch_text as varchar) as "Epoch"
        , cast(ra_of_asc_node as double) as "RaOfAscNode"
        , cast(arg_of_pericenter as double) as "ArgOfPericenter"
        , cast(mean_anomaly as double) as "MeanAnomaly"
        , cast(bstar as double) as "Bstar"
        , cast(mean_motion_dot as double) as "MeanMotionDot"
        , cast(mean_motion_ddot as double) as "MeanMotionDdot"
        , cast(rev_at_epoch as bigint) as "RevAtEpoch"
        , cast(element_set_no as bigint) as "ElementSetNo"
        , cast(ephemeris_type as bigint) as "EphemerisType"
        , cast(classification_type as varchar) as "ClassificationType"
        , cast(object_id as varchar) as "ObjectId"
    from cte_app_columns
)

select * from cte_final
order by "SatCatId"
