-- 1:1 with raw_jsr.sites: rename + cast only.
with cte_final as (
    select
        {{ helper__clean_gcat_text('Site') }} as site_code
        , {{ helper__clean_gcat_text('Code') }} as site_legacy_code
        , {{ helper__clean_gcat_text('UCode') }} as site_ucode
        , {{ helper__clean_gcat_text('Type') }} as site_type
        , {{ helper__clean_gcat_text('StateCode') }} as site_state_code
        , {{ helper__clean_gcat_text('TStart') }} as site_start_date_raw
        , {{ helper__clean_gcat_text('TStop') }} as site_stop_date_raw
        , {{ helper__clean_gcat_text('ShortName') }} as site_short_name
        , {{ helper__clean_gcat_text('Name') }} as site_name
        , {{ helper__clean_gcat_text('Location') }} as site_location
        , {{ helper__cast_gcat_value('Longitude', 'double') }} as site_longitude
        , {{ helper__cast_gcat_value('Latitude', 'double') }} as site_latitude
        , {{ helper__cast_gcat_value('Error', 'double') }} as site_location_error_deg
        , {{ helper__clean_gcat_text('Parent') }} as site_operator_code
        , {{ helper__clean_gcat_text('ShortEName') }} as site_short_name_en
        , {{ helper__clean_gcat_text('EName') }} as site_full_name_en
        , {{ helper__clean_gcat_text('Group') }} as site_group
        , {{ helper__clean_gcat_text('UName') }} as site_full_name_unicode
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _run_id
    from {{ source('jsr', 'sites') }}
)

select * from cte_final
