-- One row per GCAT organisation code, with its display name, type, class, location and active dates.
with cte_int__jsr__org_organisations as (
    select
        org_code
        , org_ucode
        , org_state_code
        , org_type
        , org_class
        , org_display_name
        , org_display_full_name
        , org_short_name
        , org_full_name
        , org_short_name_en
        , org_full_name_en
        , org_location
        , org_latitude
        , org_longitude
        , org_parent_code
        , org_start_date
        , org_start_date_start
        , org_start_date_end
        , org_start_date_precision
        , org_stop_date
        , org_stop_date_start
        , org_stop_date_end
        , org_stop_date_precision
        , flag_org_active
        , flag_country_like
        , _source_updated_at
    from {{ ref('int__jsr__org_organisations') }}
)

, cte_final as (
    select
        cast(org_code as varchar) as org_code
        , cast(org_ucode as varchar) as org_ucode
        , cast(org_state_code as varchar) as org_state_code
        , cast(org_type as varchar) as org_type
        , cast(org_class as varchar) as org_class
        , cast(org_display_name as varchar) as org_display_name
        , cast(org_display_full_name as varchar) as org_display_full_name
        , cast(org_short_name as varchar) as org_short_name
        , cast(org_full_name as varchar) as org_full_name
        , cast(org_short_name_en as varchar) as org_short_name_en
        , cast(org_full_name_en as varchar) as org_full_name_en
        , cast(org_location as varchar) as org_location
        , cast(org_latitude as double) as org_latitude
        , cast(org_longitude as double) as org_longitude
        , cast(org_parent_code as varchar) as org_parent_code
        , cast(org_start_date as timestamp) as org_start_date
        , cast(org_start_date_start as timestamp) as org_start_date_start
        , cast(org_start_date_end as timestamp) as org_start_date_end
        , cast(org_start_date_precision as varchar) as org_start_date_precision
        , cast(org_stop_date as timestamp) as org_stop_date
        , cast(org_stop_date_start as timestamp) as org_stop_date_start
        , cast(org_stop_date_end as timestamp) as org_stop_date_end
        , cast(org_stop_date_precision as varchar) as org_stop_date_precision
        , cast(flag_org_active as boolean) as flag_org_active
        , cast(flag_country_like as boolean) as flag_country_like
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_int__jsr__org_organisations
)

select * from cte_final
