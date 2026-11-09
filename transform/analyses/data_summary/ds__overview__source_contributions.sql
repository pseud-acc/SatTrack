-- Overview tab: which publisher supplied each resolved field, read from the mart's provenance columns.
-- The publisher comes from the provenance value's prefix, so new methods are picked up without a list.
with cte_fct__satellite_master as (
    select
        object_type_source
        , launch_date_source
        , status_source
        , owner_country_source
        , jcat_link_method
    from {{ ref('fct__satellite_master') }}
)

, cte_provenance as (
    select
        p.provenance.field as field
        , p.provenance.method as method
    from cte_fct__satellite_master
    cross join unnest([
        {'field': 'object_type', 'method': object_type_source}
        , {'field': 'launch_date', 'method': launch_date_source}
        , {'field': 'status', 'method': status_source}
        , {'field': 'owner_country', 'method': owner_country_source}
        , {'field': 'gcat link (jcat)', 'method': jcat_link_method}
    ]) as p(provenance)
)

, cte_publisher as (
    select
        field
        , case
            when method like 'spacetrack%' then 'Space-Track'
            when method like 'gcat%' or method like 's_norad%' then 'GCAT'
            when method like 'iso%' then 'ISO 3166 (pycountry)'
            else 'Not resolved'
        end as publisher
    from cte_provenance
)

, cte_final as (
    select
        field
        , publisher
        , count(*) as objects
    from cte_publisher
    group by
        field
        , publisher
)

select * from cte_final
