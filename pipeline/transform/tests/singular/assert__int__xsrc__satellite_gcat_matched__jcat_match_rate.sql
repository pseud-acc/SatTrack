-- Fails when fewer than var('min_jsr_match_rate') of GP objects link to a GCAT JCAT (plan section 15).
with cte_int__xsrc__satellite_gcat_matched as (
    select
        satcat_id
        , jcat
    from {{ ref('int__xsrc__satellite_gcat_matched') }}
)

, cte_match_rate as (
    select
        count(*) as n_objects
        , count(jcat) as n_matched
        , count(jcat) / nullif(count(*), 0) as match_rate
    from cte_int__xsrc__satellite_gcat_matched
)

select 'jcat_match_rate' as check_name, n_objects, n_matched, match_rate, {{ var('min_jsr_match_rate') }} as min_match_rate
from cte_match_rate
where coalesce(match_rate, 0) < {{ var('min_jsr_match_rate') }}
