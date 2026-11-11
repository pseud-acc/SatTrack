-- Objects tab: distribution of payload launch mass on a log scale (bins of 0.1 in log10 kg).
with cte_fct__satellite_master as (
    select
        object_type
        , mass_kg
        , flag_mass_estimated
    from {{ ref('fct__satellite_master') }}
)

, cte_binned as (
    select
        floor(log10(mass_kg) * 10) / 10 as log10_mass_kg
        , case
            when flag_mass_estimated = 1 then 'Estimated'
            else 'Reported'
        end as mass_basis
    from cte_fct__satellite_master
    where object_type = 'PAYLOAD'
        and mass_kg > 0
)

, cte_final as (
    select
        log10_mass_kg
        , mass_basis
        , count(*) as payloads
    from cte_binned
    group by
        log10_mass_kg
        , mass_basis
    order by log10_mass_kg
)

select * from cte_final
