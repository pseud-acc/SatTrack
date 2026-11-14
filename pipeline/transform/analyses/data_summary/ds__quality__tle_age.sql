-- Data quality tab: age of each object's latest element set at load time, in bands, by object type.
with cte_fct__satellite_master as (
    select
        object_type
        , tle_age_days
    from {{ ref('fct__satellite_master') }}
)

, cte_banded as (
    select
        object_type
        , case
            when tle_age_days is null then 5
            when tle_age_days < 1 then 0
            when tle_age_days < 3 then 1
            when tle_age_days < 7 then 2
            when tle_age_days < 30 then 3
            else 4
        end as band_order
    from cte_fct__satellite_master
)

, cte_final as (
    select
        band_order
        , case band_order
            when 0 then 'under 1 day'
            when 1 then '1-3 days'
            when 2 then '3-7 days'
            when 3 then '7-30 days'
            when 4 then '30+ days'
            else 'no epoch'
        end as tle_age_band
        , object_type
        , count(*) as objects
    from cte_banded
    group by
        band_order
        , object_type
    order by band_order
)

select * from cte_final
