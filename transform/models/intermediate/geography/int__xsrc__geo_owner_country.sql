-- One row per Space-Track country/organisation code (boxscore), resolved deterministically with no
-- alias list (plan section 15.1): each part of the Space-Track name (split on '/') is matched, by exact name key
-- (full key, then reduced key), against the ISO 3166-1 names, then the GeoNames country names, then the
-- ISO 3166-3 former countries (int__xsrc__geo_country_name_keys); exact keys only, no near/fuzzy match (user, 2026-11-08);
-- parts that match nothing -> title-cased Space-Track name.
with cte_stg__spacetrack__boxscore as (
    select
        country_code
        , spacetrack_country_name
    from {{ ref('stg__spacetrack__boxscore') }}
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

, cte_boxscore_name_parts as ( -- 'FRANCE/GERMANY' -> one row per part
    select
        b.country_code
        , b.spacetrack_country_name
        , trim(p.part) as part
        , p.ord
    from cte_stg__spacetrack__boxscore as b
    cross join unnest(string_split(b.spacetrack_country_name, '/')) with ordinality as p(part, ord)
)

, cte_name_parts_matched as ( -- best match per part: list order (ISO, GeoNames, former), then full key before reduced key
    select
        parts.country_code
        , parts.spacetrack_country_name
        , parts.part
        , parts.ord
        , keys.name_tier
        , keys.matched_iso_code
        , keys.matched_country_name
    from cte_boxscore_name_parts as parts
    left join cte_int__xsrc__geo_country_name_keys as keys
        on (keys.key_type = 'full' and keys.name_key = {{ helper__build_country_key_full('parts.part') }})
        or (keys.key_type = 'reduced' and keys.name_key = {{ helper__build_country_key_reduced('parts.part') }})
    qualify row_number() over (
        partition by parts.country_code, parts.ord
        order by
            case keys.name_tier when 'iso' then 1 when 'geonames_name' then 2 when 'iso_historic' then 3 end
            , case keys.key_type when 'full' then 1 else 2 end
    ) = 1
)

, cte_owner_codes_matched as ( -- one row per code: how many parts matched, and the last list any part needed
    select
        country_code
        , any_value(spacetrack_country_name) as spacetrack_country_name
        , count(*) as n_parts
        , count(matched_iso_code) as n_matched
        , max(case name_tier when 'iso' then 1 when 'geonames_name' then 2 when 'iso_historic' then 3 end) as last_tier
        , list(matched_iso_code order by ord) filter (where matched_iso_code is not null) as iso_codes
        , string_agg(matched_country_name, ' / ' order by ord) as iso_names
    from cte_name_parts_matched
    group by country_code
)

, cte_final as (
    select
        country_code
        , spacetrack_country_name
        , case
            when country_code = 'TBD' then 'Unknown'
            when n_matched = n_parts then iso_names
            else {{ helper__title_case_name('spacetrack_country_name') }}
        end as owner_country
        , case when n_matched = n_parts then iso_codes else cast([] as varchar[]) end as owner_country_codes
        , country_code <> 'TBD' and n_matched < n_parts as owner_country_is_org
        , case
            when country_code = 'TBD' then 'unknown'
            when n_matched < n_parts then 'spacetrack_name'
            when last_tier = 2 then 'geonames_name'
            when last_tier = 3 then 'iso_historic'
            when n_parts = 1 then 'iso_exact'
            else 'iso_split'
        end as owner_country_method
        , {{ helper__audit_fields() }}
    from cte_owner_codes_matched
)

select * from cte_final
