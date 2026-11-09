-- One row per ISO 3166 country (current and historic): codes and display names. The app's country dimension.
with cte_int__pycountry__geo_countries as (
    select
        country_key
        , iso_alpha2
        , iso_alpha3
        , iso_alpha4
        , iso_numeric
        , country_display_name
        , country_name
        , country_official_name
        , is_historic
        , iso_withdrawal_date
    from {{ ref('int__pycountry__geo_countries') }}
)

, cte_final as (
    select
        cast(country_key as varchar) as country_key
        , cast(iso_alpha2 as varchar) as iso_alpha2
        , cast(iso_alpha3 as varchar) as iso_alpha3
        , cast(iso_alpha4 as varchar) as iso_alpha4
        , cast(iso_numeric as varchar) as iso_numeric
        , cast(country_display_name as varchar) as country_display_name
        , cast(country_name as varchar) as country_name
        , cast(country_official_name as varchar) as country_official_name
        , cast(is_historic as boolean) as is_historic
        , cast(iso_withdrawal_date as date) as iso_withdrawal_date
        , {{ helper__audit_fields() }}
    from cte_int__pycountry__geo_countries
)

select * from cte_final
