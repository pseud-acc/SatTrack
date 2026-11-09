-- 1:1 with raw_pycountry.iso_countries (pinned pycountry export): rename + cast only.
with cte_final as (
    select
        cast(nullif(alpha_2, '') as varchar) as iso_alpha2
        , cast(nullif(alpha_3, '') as varchar) as iso_alpha3
        , cast(nullif("numeric", '') as varchar) as iso_numeric
        , cast("name" as varchar) as country_name
        , cast(nullif(official_name, '') as varchar) as country_official_name
        , cast(nullif(common_name, '') as varchar) as country_common_name
        , cast(nullif(alpha_4, '') as varchar) as iso_alpha4
        , try_cast(nullif(withdrawal_date, '') as date) as iso_withdrawal_date
        , cast(is_historic as boolean) as is_historic
        , cast(_loaded_at as timestamp) as _loaded_at
        , _source_url
    from {{ source('pycountry', 'iso_countries') }}
)

select * from cte_final
