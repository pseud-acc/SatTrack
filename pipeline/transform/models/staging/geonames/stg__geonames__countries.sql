-- 1:1 with raw_geonames.countries (pinned geonamescache export): rename + cast only.
with cte_final as (
    select
        cast(geonameid as integer) as geonameid
        , cast("name" as varchar) as geonames_country_name
        , cast(iso as varchar) as iso_alpha2
        , cast(iso3 as varchar) as iso_alpha3
        , cast(_loaded_at as timestamp) as _loaded_at
        , _source_url
    from {{ source('geonames', 'countries') }}
)

select * from cte_final
