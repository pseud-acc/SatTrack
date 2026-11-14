-- 1:1 with raw_spacetrack.gp: rename + cast only (no filters, joins or derivations).
with cte_final as (
    select
        cast("NORAD_CAT_ID" as integer) as satcat_id
        , cast(nullif("OBJECT_NAME", '') as varchar) as object_name
        , cast(nullif("OBJECT_ID", '') as varchar) as object_id
        , cast(nullif("OBJECT_TYPE", '') as varchar) as object_type
        , cast(nullif("COUNTRY_CODE", '') as varchar) as country_code
        , try_cast(nullif("LAUNCH_DATE", '') as date) as launch_date
        , cast(nullif("SITE", '') as varchar) as launch_site
        , try_cast(nullif("DECAY_DATE", '') as date) as decay_date
        , try_cast("EPOCH" as timestamp) as epoch
        , try_cast("MEAN_MOTION" as double) as mean_motion
        , try_cast("ECCENTRICITY" as double) as eccentricity
        , try_cast("INCLINATION" as double) as inclination
        , try_cast("RA_OF_ASC_NODE" as double) as ra_of_asc_node
        , try_cast("ARG_OF_PERICENTER" as double) as arg_of_pericenter
        , try_cast("MEAN_ANOMALY" as double) as mean_anomaly
        , try_cast("BSTAR" as double) as bstar
        , try_cast("MEAN_MOTION_DOT" as double) as mean_motion_dot
        , try_cast("MEAN_MOTION_DDOT" as double) as mean_motion_ddot
        , try_cast("SEMIMAJOR_AXIS" as double) as semimajor_axis
        , try_cast("PERIOD" as double) as orbital_period
        , try_cast("APOAPSIS" as double) as apoapsis
        , try_cast("PERIAPSIS" as double) as periapsis
        , cast(nullif("RCS_SIZE", '') as varchar) as rcs_size
        , cast(nullif("MEAN_ELEMENT_THEORY", '') as varchar) as mean_element_theory
        , cast(nullif("CLASSIFICATION_TYPE", '') as varchar) as classification_type
        , try_cast("EPHEMERIS_TYPE" as integer) as ephemeris_type
        , try_cast("ELEMENT_SET_NO" as integer) as element_set_no
        , try_cast("REV_AT_EPOCH" as integer) as rev_at_epoch
        , cast(nullif("CENTER_NAME", '') as varchar) as center_name
        , cast(nullif("REF_FRAME", '') as varchar) as ref_frame
        , cast(nullif("TIME_SYSTEM", '') as varchar) as time_system
        , cast(nullif("CCSDS_OMM_VERS", '') as varchar) as ccsds_omm_vers
        , cast(nullif("COMMENT", '') as varchar) as omm_comment
        , try_cast("CREATION_DATE" as timestamp) as creation_date
        , cast(nullif("ORIGINATOR", '') as varchar) as originator
        , try_cast("FILE" as bigint) as file_no
        , try_cast("GP_ID" as bigint) as gp_id
        , cast(nullif("TLE_LINE0", '') as varchar) as tle_line_0
        , cast(nullif("TLE_LINE1", '') as varchar) as tle_line_1
        , cast(nullif("TLE_LINE2", '') as varchar) as tle_line_2
        , cast(_loaded_at as timestamp) as _loaded_at
        , _run_id
        , _source_url
    from {{ source('spacetrack', 'gp') }}
)

select * from cte_final
