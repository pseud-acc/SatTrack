-- 1:1 with raw_geonames.cities (pinned geonamescache export): rename + cast only.
with cte_final as (
    select
        cast(geonameid as integer) as geonameid
        , cast("name" as varchar) as city_name
        , cast(countrycode as varchar) as iso_alpha2
        , cast(latitude as double) as latitude
        , cast(longitude as double) as longitude
        , cast(population as bigint) as population
        , cast(_loaded_at as timestamp) as _loaded_at
        , _source_url
    from {{ source('geonames', 'cities') }}
)

select * from cte_final
