-- Data quality tab: how each resolved field was filled, from the mart's provenance columns (one row per field and method).
with cte_fct__satellite_master as (
    select
        object_type_source
        , launch_date_source
        , operational_status_source
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
        , {'field': 'operational_status', 'method': operational_status_source}
        , {'field': 'owner_country', 'method': owner_country_source}
        , {'field': 'gcat link (jcat)', 'method': jcat_link_method}
    ]) as p(provenance)
)

, cte_final as (
    select
        field
        , coalesce(method, 'null') as method
        , count(*) as objects
        , count(*) / sum(count(*)) over (partition by field) as share
    from cte_provenance
    group by
        field
        , coalesce(method, 'null')
    order by
        field
        , objects desc
)

select * from cte_final
