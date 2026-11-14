-- One row per GCAT object from the Current Catalog (all object types).
with cte_stg__jsr__currentcat as (
    select
        jcat
        , activity_type
        , current_status
        , current_owner_code
        , current_owner_state_code
        , descent_date_raw
        , _source_updated_at
    from {{ ref('stg__jsr__currentcat') }}
)

, cte_final as (
    select
        jcat
        , case when activity_type in ('A', 'C', 'D', 'P', 'R', 'Z') then activity_type end as activity_type
        , current_status
        , current_owner_code
        , current_owner_state_code
        , {{ helper__parse_vague_date_columns('descent_date_raw', 'descent_date') }}
        -- GCAT curcols.html: DDate "If blank, the object is still in orbit."
        , cast(descent_date_raw is null as integer) as flag_gcat_in_orbit
        , _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_stg__jsr__currentcat
)

select * from cte_final
