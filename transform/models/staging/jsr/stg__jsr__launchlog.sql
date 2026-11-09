-- 1:1 with raw_jsr.launchlog: rename + cast only (vague dates kept as text).
with cte_final as (
    select
        {{ helper__clean_gcat_text('Launch_Tag') }} as launch_tag
        , {{ helper__clean_gcat_text('Launch_Date') }} as launch_datetime_raw
        , {{ helper__clean_gcat_text('Piece') }} as cospar_id
        , {{ helper__clean_gcat_text('Type') }} as sat_type
        , {{ helper__clean_gcat_text('Name') }} as gcat_name
        , {{ helper__clean_gcat_text('PLName') }} as pre_launch_name
        , {{ helper__clean_gcat_text('JCAT') }} as jcat
        , {{ helper__clean_gcat_text('SatOwner') }} as current_owner_code
        , {{ helper__clean_gcat_text('SatState') }} as current_state_code
        , {{ helper__clean_gcat_text('LV_Type') }} as lv_type
        , {{ helper__clean_gcat_text('Flight_ID') }} as flight_id
        , {{ helper__clean_gcat_text('Platform') }} as launch_platform
        , {{ helper__clean_gcat_text('Launch_Site') }} as site_code_raw
        , {{ helper__clean_gcat_text('Launch_Pad') }} as launch_pad
        , {{ helper__clean_gcat_text('Ascent_Site') }} as ascent_site_code
        , {{ helper__clean_gcat_text('Ascent_Pad') }} as ascent_pad
        , {{ helper__clean_gcat_text('Agency') }} as launch_agency_code
        , {{ helper__clean_gcat_text('LVState') }} as launch_agency_country
        , {{ helper__clean_gcat_text('Launch_Code') }} as launch_code
        , {{ helper__clean_gcat_text('LTCite') }} as launch_time_ref
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _run_id
    from {{ source('jsr', 'launchlog') }}
)

select * from cte_final
