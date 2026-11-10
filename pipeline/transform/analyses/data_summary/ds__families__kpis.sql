-- Programme families tab: one-row figures for the programme families (satellite_program_family).
-- A "large" family is one with at least 50 payloads.
with cte_fct__satellite_master as (
    select
        object_type
        , satellite_program_family
    from {{ ref('fct__satellite_master') }}
)

, cte_payloads as (
    select
        satellite_program_family
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
)

, cte_family_sizes as (
    select
        satellite_program_family
        , count(*) as payloads
        , count(*) >= 50 as is_large
    from cte_payloads
    group by satellite_program_family
)

, cte_final as (
    select
        sum(payloads) as payloads
        , sum(payloads) filter (where satellite_program_family is not null) as payloads_with_family
        , count(*) filter (where is_large and satellite_program_family is not null) as large_families
        , coalesce(sum(payloads) filter (where is_large and satellite_program_family is not null), 0) as payloads_in_large_families
        , coalesce(sum(payloads) filter (where is_large and satellite_program_family is not null), 0) / sum(payloads) as share_in_large_families
    from cte_family_sizes
)

select * from cte_final
