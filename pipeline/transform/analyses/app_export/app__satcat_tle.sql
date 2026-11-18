-- App export: satcat_tle.csv, the satellite file the live SatTrack Dash app loads (S3 app/satcat_tle.csv, read with
-- a plain pandas.read_csv, no dtypes or parse_dates; app/core/state.py).
-- Columns, order and value formats follow the legacy pipeline's export (removed in 2.2.0), less StatusCode, UcsData
-- and OrbitClassEstimated: the app never read them and this pipeline has no source for them.
-- The app drops every row that has any missing value (DataFrame.dropna after propagation), so no column may be empty:
-- text gaps are 'Unknown' and number gaps are -1.0, as in the old file.
-- Scope matches the old app: Earth-orbiting payloads with a TLE and a positive period.
-- Two sources, so positions never wait for the GCAT details: what each satellite is (name, owner, status, purpose)
-- comes from fct__satellite_master (enrichment unit), and where it is (TLE lines, period, inclination) from
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
        , orbital_period
        , inclination
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
        , round(gp.inclination, 2) as inclination
        , mass_kg
        , gp.tle_line_1
        , gp.tle_line_2
    from cte_fct__satellite_master as sat
    inner join cte_fct__gp_elements as gp
        on sat.satcat_id = gp.satcat_id
    where sat.object_type = 'PAYLOAD'
        and sat.flag_in_orbit = 1
        and gp.tle_line_1 is not null
        and gp.tle_line_2 is not null
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
        , coalesce(inclination, -1.0) as inclination
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
        -- parsed from TLE line 2 exactly as the old export did: TLE2[52:63] and '0.' + TLE2[26:33]
        , cast(substr(tle_line_2, 53, 11) as double) as mean_motion
        , cast('0.' || substr(tle_line_2, 27, 7) as double) as eccentricity
        , orbit_class
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
    from cte_app_columns
)

select * from cte_final
order by "SatCatId"
