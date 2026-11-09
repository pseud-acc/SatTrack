-- App export: satcat_tle.csv, the satellite file the live SatTrack Dash app loads (repo path dat/clean/satcat_tle.csv,
-- read with a plain pandas.read_csv, no dtypes or parse_dates).
-- Same 20 columns, order and value formats as the old export (SatTrack src/pipeline/app_data_export/export_app_data.py).
-- The app drops every row that has any missing value (DataFrame.dropna after propagation), so no column may be empty:
-- text gaps are 'Unknown' and number gaps are -1.0, as in the old file.
-- Scope matches the old app: Earth-orbiting payloads with a TLE and a positive period.
with cte_fct__satellite_master as (
    select
        satcat_id
        , object_name
        , object_type
        , flag_in_orbit
        , status
        , launch_year
        , owner_country
        , site_location_country
        , ownership_class_labels
        , mission_category_labels
        , lv_brand
        , orbit_class
        , orbital_period
        , inclination
        , mass_kg
        , tle_line_1
        , tle_line_2
    from {{ ref('fct__satellite_master') }}
)

, cte_app_scope as (
    select
        satcat_id
        , object_name
        , status
        , launch_year
        , owner_country
        , site_location_country
        , ownership_class_labels
        , mission_category_labels
        , lv_brand
        , orbit_class
        , round(orbital_period, 2) as orbital_period
        , round(inclination, 2) as inclination
        , mass_kg
        , tle_line_1
        , tle_line_2
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and flag_in_orbit
        and tle_line_1 is not null
        and tle_line_2 is not null
        and orbital_period > 0
        and launch_year is not null
)

, cte_app_columns as (
    select
        satcat_id
        , coalesce(object_name, 'Unknown') as object_name
        , launch_year
        , orbital_period
        , coalesce(mass_kg, -1.0) as launch_mass
        -- CelesTrak operational status code: no source in the new pipeline; 'UNK' is the old file's own "no code" value
        , 'UNK' as status_code
        , coalesce(inclination, -1.0) as inclination
        , coalesce(status, 'Inactive') as status
        -- 1 when UCS data matched in the old pipeline; UCS is not a source of the new pipeline
        , 0 as ucs_data
        -- the old CelesTrak-import rule, period only: LEO <= 128 min, MEO < 1400, GSO 1400-1500, HEO above
        , case
            when orbital_period <= 128 then 'LEO'
            when orbital_period < 1400 then 'MEO'
            when orbital_period <= 1500 then 'GSO'
            else 'HEO'
        end as orbit_class_estimated
        , coalesce(site_location_country, 'Unknown') as launch_site_country
        , coalesce(owner_country, 'Unknown') as owner
        -- labels sorted and joined with '/', as the old pipeline standardised UCS Users
        , coalesce(nullif(array_to_string(list_sort(ownership_class_labels), '/'), ''), 'Unknown') as use_type
        -- joined with '/': the app splits Purpose on '/' to build its multi-select filter
        , coalesce(nullif(array_to_string(mission_category_labels, '/'), ''), 'Unknown') as purpose
        , coalesce(lv_brand, 'Unknown') as launch_vehicle_class
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
        , cast(status_code as varchar) as "StatusCode"
        , cast(inclination as double) as "Inclination"
        , cast(status as varchar) as "Status"
        , cast(ucs_data as bigint) as "UcsData"
        , cast(orbit_class_estimated as varchar) as "OrbitClassEstimated"
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
