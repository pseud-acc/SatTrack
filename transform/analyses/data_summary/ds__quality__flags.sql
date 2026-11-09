-- Data quality tab: objects carrying each caution flag in the mart (flag definitions: see the field catalogue).
with cte_fct__satellite_master as (
    select
        flag_gcat_matched
        , flag_orbit_conflict
        , flag_catalog_match_uncertain
        , flag_mass_estimated
    from {{ ref('fct__satellite_master') }}
)

, cte_flags as (
    select
        f.flag.name as flag
        , f.flag.raised as raised
    from cte_fct__satellite_master
    cross join unnest([
        {'name': 'flag_gcat_matched = false', 'raised': not flag_gcat_matched}
        , {'name': 'flag_orbit_conflict', 'raised': flag_orbit_conflict}
        , {'name': 'flag_catalog_match_uncertain', 'raised': flag_catalog_match_uncertain}
        , {'name': 'flag_mass_estimated', 'raised': flag_mass_estimated}
    ]) as f(flag)
)

, cte_final as (
    select
        flag
        , count(*) filter (where raised) as objects
        , avg(cast(coalesce(raised, false) as integer)) as share
    from cte_flags
    group by flag
    order by objects desc
)

select * from cte_final
