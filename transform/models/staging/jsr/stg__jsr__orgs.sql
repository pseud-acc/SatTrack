-- 1:1 with raw_jsr.orgs: rename + cast only.
with cte_final as (
    select
        {{ helper__clean_gcat_text('Code') }} as org_code
        , {{ helper__clean_gcat_text('UCode') }} as org_ucode
        , {{ helper__clean_gcat_text('StateCode') }} as org_state_code
        , {{ helper__clean_gcat_text('Type') }} as org_type
        , {{ helper__clean_gcat_text('Class') }} as org_class
        , {{ helper__clean_gcat_text('TStart') }} as org_start_date_raw
        , {{ helper__clean_gcat_text('TStop') }} as org_stop_date_raw
        , {{ helper__clean_gcat_text('ShortName') }} as org_short_name
        , {{ helper__clean_gcat_text('Name') }} as org_full_name
        , {{ helper__clean_gcat_text('Location') }} as org_location
        , {{ helper__cast_gcat_value('Longitude', 'double') }} as org_longitude
        , {{ helper__cast_gcat_value('Latitude', 'double') }} as org_latitude
        , {{ helper__cast_gcat_value('Error', 'double') }} as org_location_error_deg
        , {{ helper__clean_gcat_text('Parent') }} as org_parent_code
        , {{ helper__clean_gcat_text('ShortEName') }} as org_short_name_en
        , {{ helper__clean_gcat_text('EName') }} as org_full_name_en
        , {{ helper__clean_gcat_text('UName') }} as org_full_name_unicode
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _run_id
    from {{ source('jsr', 'orgs') }}
)

select * from cte_final
