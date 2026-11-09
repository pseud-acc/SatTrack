-- One row per object per owner country: owner_country_codes of the GP object, one row per code in list order, with the
-- dim__country key of the country (int__pycountry__geo_countries). A code is an ISO 3166-1 alpha-2 code (current
-- country) or an ISO 3166-3 alpha-4 code (former country). Objects whose owner is an organisation or unresolved have
-- no codes and so no rows. A code with no ISO country keeps its row with a NULL country_key (the key test fails).
with cte_int__xsrc__satellite_gcat_matched as (
    select
        satcat_id
        , owner_country_codes
        , owner_country_source
    from {{ ref('int__xsrc__satellite_gcat_matched') }}
)

, cte_int__pycountry__geo_countries as (
    select
        country_key
        , iso_alpha2
        , iso_alpha4
        , is_historic
    from {{ ref('int__pycountry__geo_countries') }}
)

, cte_owner_country_codes as ( -- one row per code in each owner_country_codes list
    select
        sat.satcat_id
        , sat.owner_country_source
        , c.code as owner_country_iso_code
        , cast(c.ord as integer) as owner_country_iso_code_ord
    from cte_int__xsrc__satellite_gcat_matched as sat
    cross join unnest(sat.owner_country_codes) with ordinality as c(code, ord)
)

, cte_final as (
    select
        {{ dbt_utils.generate_surrogate_key(['m.satcat_id', "'owner'", 'm.owner_country_iso_code_ord', 'm.owner_country_iso_code']) }} as map_id
        , m.satcat_id
        , g.country_key
        , m.owner_country_iso_code
        , m.owner_country_iso_code_ord
        , m.owner_country_source
        , {{ helper__audit_fields() }}
    from cte_owner_country_codes as m
    left join cte_int__pycountry__geo_countries as g
        on (not g.is_historic and g.iso_alpha2 = m.owner_country_iso_code)
        or (g.is_historic and g.iso_alpha4 = m.owner_country_iso_code)
)

select * from cte_final
