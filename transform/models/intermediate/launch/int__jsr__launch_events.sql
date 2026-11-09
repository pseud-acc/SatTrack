-- One row per payload launch (GCAT launch log). Launch_Code is split into the documented category
-- (O, M, T, A, S, D, H, R, X, Y; undocumented letters -> NULL) and the success code.
with cte_stg__jsr__launchlog as (
    select
        jcat
        , launch_tag
        , launch_datetime_raw
        , cospar_id
        , sat_type
        , site_code_raw
        , launch_pad
        , ascent_site_code
        , ascent_pad
        , launch_platform
        , lv_type
        , flight_id
        , launch_agency_code
        , launch_agency_country
        , launch_code
        , launch_time_ref
        , current_owner_code
        , current_state_code
        , _source_updated_at
    from {{ ref('stg__jsr__launchlog') }}
)

, cte_final as (
    select
        jcat
        , launch_tag
        , {{ helper__parse_vague_date_columns('launch_datetime_raw', 'launch_datetime') }}
        , cospar_id
        -- GCAT llog.html: a '?' in SatType position 9 marks an arbitrary match to the launch's catalog slots
        , coalesce(substr(sat_type, 9, 1) = '?', false) as flag_catalog_match_uncertain
        , rtrim(site_code_raw, '?') as site_code
        , coalesce(site_code_raw like '%?', false) as flag_site_uncertain
        , launch_pad
        , ascent_site_code
        , ascent_pad
        , launch_platform
        , lv_type
        , {{ helper__derive_lv_brand('lv_type') }} as lv_brand
        , flight_id
        , launch_agency_code
        , launch_agency_country
        , launch_code
        , case when left(launch_code, 1) in ('O', 'M', 'T', 'A', 'S', 'D', 'H', 'R', 'X', 'Y') then left(launch_code, 1) end as launch_category
        , nullif(substr(launch_code, 2), '') as launch_success_code
        , launch_time_ref
        , current_owner_code
        , current_state_code
        , _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_stg__jsr__launchlog
)

select * from cte_final
