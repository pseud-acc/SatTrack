-- One row per ISO 3166 country, current (3166-1) and historic (3166-3), from the pinned pycountry export.
with cte_stg__pycountry__iso_countries as (
    select
        iso_alpha2
        , iso_alpha3
        , iso_alpha4
        , iso_numeric
        , country_name
        , country_official_name
        , country_common_name
        , is_historic
        , iso_withdrawal_date
    from {{ ref('stg__pycountry__iso_countries') }}
)

, cte_final as (
    select
        iso_alpha3 || case when is_historic then '-H' else '' end as country_key
        , iso_alpha2
        , iso_alpha3
        , iso_alpha4
        , iso_numeric
        , coalesce(country_common_name, country_name) as country_display_name
        , country_name
        , country_official_name
        , is_historic
        , iso_withdrawal_date
        , {{ helper__audit_fields() }}
    from cte_stg__pycountry__iso_countries
    where iso_alpha3 is not null
)

select * from cte_final
