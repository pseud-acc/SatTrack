-- One row per payload launch (GCAT launch log). Launch_Code is split into the documented category
-- (O, M, T, A, S, D, H, R, X, Y; undocumented letters -> NULL) and the success code.
-- A JCAT that GCAT gives to more than one row (a key typo, e.g. F01824 and F01834 on launch 2026-F07 in Nov 2026)
-- keeps its first row in GCAT's file order; the later rows are dropped. The staging check
-- mh__stg__jsr__launchlog__pk_unique reports them (warn) and fails the build above 10 such JCATs.
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
        , launch_vehicle_type
        , flight_id
        , launch_agency_code
        , launch_agency_country
        , launch_code
        , launch_time_ref
        , current_owner_code
        , current_owner_state_code
        , _source_updated_at
        , _source_row_number
    from {{ ref('stg__jsr__launchlog') }}
)

, cte_first_row_per_jcat as ( -- a repeated JCAT keeps its first row in the source file
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
        , launch_vehicle_type
        , flight_id
        , launch_agency_code
        , launch_agency_country
        , launch_code
        , launch_time_ref
        , current_owner_code
        , current_owner_state_code
        , _source_updated_at
    from cte_stg__jsr__launchlog
    qualify row_number() over (partition by jcat order by _source_row_number) = 1
)

, cte_final as (
    select
        jcat
        , launch_tag
        , {{ helper__parse_vague_date_columns('launch_datetime_raw', 'launch_datetime') }}
        , cospar_id
        -- GCAT llog.html: a '?' in SatType position 9 marks an arbitrary match to the launch's catalog slots
        , cast(coalesce(substr(sat_type, 9, 1) = '?', false) as integer) as flag_catalog_match_uncertain
        , rtrim(site_code_raw, '?') as site_code
        , cast(coalesce(site_code_raw like '%?', false) as integer) as flag_site_uncertain
        , launch_pad
        , ascent_site_code
        , ascent_pad
        , launch_platform
        , launch_vehicle_type
        , {{ helper__derive_lv_brand('launch_vehicle_type') }} as launch_vehicle_brand
        , flight_id
        , launch_agency_code
        , launch_agency_country
        , launch_code
        , case when left(launch_code, 1) in ('O', 'M', 'T', 'A', 'S', 'D', 'H', 'R', 'X', 'Y') then left(launch_code, 1) end as launch_category
        , nullif(substr(launch_code, 2), '') as launch_success_code
        , launch_time_ref
        , current_owner_code
        , current_owner_state_code
        , _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_first_row_per_jcat
)

select * from cte_final
