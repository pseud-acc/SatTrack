-- One row per GCAT country-like organisation (CY, IGO, AP) whose English name resolves to a country, using the same
-- name match as the Space-Track owner country (int__xsrc__geo_country_name_keys): the English short name is tried
-- first, then the English full name; within a name, ISO 3166-1, then GeoNames, then ISO 3166-3, full key before reduced key.
with cte_int__jsr__org_organisations as (
    select
        org_code
        , org_short_name_en
        , org_full_name_en
        , flag_country_like
    from {{ ref('int__jsr__org_organisations') }}
)

, cte_int__xsrc__geo_country_name_keys as (
    select
        name_tier
        , key_type
        , name_key
        , matched_iso_code
        , matched_country_name
    from {{ ref('int__xsrc__geo_country_name_keys') }}
)

, cte_org_name_candidates as ( -- the English names of each country-like org, in the order they are tried
    select
        org_code
        , 1 as candidate_rank
        , org_short_name_en as candidate_name
    from cte_int__jsr__org_organisations
    where flag_country_like = 1 and org_short_name_en is not null
    union all
    select
        org_code
        , 2 as candidate_rank
        , org_full_name_en as candidate_name
    from cte_int__jsr__org_organisations
    where flag_country_like = 1 and org_full_name_en is not null
)

, cte_org_names_matched as ( -- best match per org
    select
        cand.org_code
        , keys.name_tier
        , keys.matched_iso_code
        , keys.matched_country_name
    from cte_org_name_candidates as cand
    inner join cte_int__xsrc__geo_country_name_keys as keys
        on (keys.key_type = 'full' and keys.name_key = {{ helper__build_country_key_full('cand.candidate_name') }})
        or (keys.key_type = 'reduced' and keys.name_key = {{ helper__build_country_key_reduced('cand.candidate_name') }})
    qualify row_number() over (
        partition by cand.org_code
        order by
            cand.candidate_rank
            , case keys.name_tier when 'iso' then 1 when 'geonames_name' then 2 else 3 end
            , case keys.key_type when 'full' then 1 else 2 end
    ) = 1
)

, cte_final as (
    select
        org_code as state_code
        , matched_country_name as owner_country
        , [matched_iso_code] as owner_country_codes
        , case name_tier
            when 'iso' then 'iso_exact'
            when 'geonames_name' then 'geonames_name'
            else 'iso_historic'
        end as owner_country_method
        , {{ helper__audit_fields() }}
    from cte_org_names_matched
)

select * from cte_final
