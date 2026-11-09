-- One row per country-name key, from three name lists tried in this order (decided 2026-11-08):
--   iso            current ISO 3166-1 names (name, official name, common name), pycountry -> alpha-2 code;
--   geonames_name  GeoNames country names (geonamescache), only for countries that also have an ISO 3166-1 row -> alpha-2 code;
--   iso_historic   former ISO 3166-3 countries, by full name and by the part of it before the first comma -> alpha-4 code.
-- Each name is keyed in full and reduced (common words removed); a key stays only when it identifies exactly one
-- country in its list. No alias list.
with cte_stg__pycountry__iso_countries as (
    select
        iso_alpha2
        , iso_alpha4
        , country_name
        , country_official_name
        , country_common_name
        , is_historic
    from {{ ref('stg__pycountry__iso_countries') }}
)

, cte_stg__geonames__countries as (
    select
        iso_alpha2
        , geonames_country_name
    from {{ ref('stg__geonames__countries') }}
)

, cte_name_variants as ( -- every name of every list, with the code it resolves to and the name to display
    select
        'iso' as name_tier
        , iso_alpha2 as iso_code
        , country_name as display_name
        , country_name as name_variant
    from cte_stg__pycountry__iso_countries
    where not is_historic
    union all
    select
        'iso' as name_tier
        , iso_alpha2 as iso_code
        , country_name as display_name
        , country_official_name as name_variant
    from cte_stg__pycountry__iso_countries
    where not is_historic and country_official_name is not null
    union all
    select
        'iso' as name_tier
        , iso_alpha2 as iso_code
        , country_common_name as display_name
        , country_common_name as name_variant
    from cte_stg__pycountry__iso_countries
    where not is_historic and country_common_name is not null
    union all
    select
        'geonames_name' as name_tier
        , g.iso_alpha2 as iso_code
        , coalesce(i.country_common_name, i.country_name) as display_name
        , g.geonames_country_name as name_variant
    from cte_stg__geonames__countries as g
    inner join cte_stg__pycountry__iso_countries as i on i.iso_alpha2 = g.iso_alpha2 and not i.is_historic
    union all
    select
        'iso_historic' as name_tier
        , iso_alpha4 as iso_code
        , split_part(country_name, ',', 1) as display_name
        , country_name as name_variant
    from cte_stg__pycountry__iso_countries
    where is_historic and iso_alpha4 is not null
    union all
    select
        'iso_historic' as name_tier
        , iso_alpha4 as iso_code
        , split_part(country_name, ',', 1) as display_name
        , split_part(country_name, ',', 1) as name_variant
    from cte_stg__pycountry__iso_countries
    where is_historic and iso_alpha4 is not null
)

, cte_name_keys as ( -- each name variant as a full key and a reduced key
    select
        name_tier
        , 'full' as key_type
        , {{ helper__build_country_key_full('name_variant') }} as name_key
        , iso_code
        , display_name
    from cte_name_variants
    union all
    select
        name_tier
        , 'reduced' as key_type
        , {{ helper__build_country_key_reduced('name_variant') }} as name_key
        , iso_code
        , display_name
    from cte_name_variants
)

, cte_final as ( -- keep only keys that identify exactly one country within their list
    select
        name_tier
        , key_type
        , name_key
        , any_value(iso_code) as matched_iso_code
        , max(display_name) as matched_country_name
        , {{ helper__audit_fields() }}
    from cte_name_keys
    where name_key <> ''
    group by name_tier, key_type, name_key
    having count(distinct iso_code) = 1
)

select * from cte_final
