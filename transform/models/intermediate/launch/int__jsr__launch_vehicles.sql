-- One row per launch vehicle name (the launch log joins on name only). GCAT's own key is name + variant;
-- the row without a variant is preferred, then the first variant. Manufacturers from every variant are
-- kept as a list (no manual override, plan section 15.1). Undocumented class values (e.g. 'B') become NULL.
with cte_stg__jsr__lv as (
    select
        lv_name
        , lv_family
        , lv_generic_name
        , lv_class
        , lv_manufacturer_code
        , lv_variant
        , lv_alias
        , lv_length_m
        , lv_diameter_m
        , lv_launch_mass_t
        , lv_leo_capacity_kg
        , lv_gto_capacity_kg
        , lv_takeoff_thrust_kn
        , _source_row_number
        , _source_updated_at
    from {{ ref('stg__jsr__lv') }}
)

, cte_int__jsr__org_organisations as (
    select
        org_code
        , org_display_name
    from {{ ref('int__jsr__org_organisations') }}
)

, cte_lv_preferred_variant as ( -- one row per name: no-variant row first, then the first variant
    select
        lv_name
        , lv_family
        , lv_generic_name
        , lv_class
        , lv_manufacturer_code
        , lv_variant
        , lv_alias
        , lv_length_m
        , lv_diameter_m
        , lv_launch_mass_t
        , lv_leo_capacity_kg
        , lv_gto_capacity_kg
        , lv_takeoff_thrust_kn
        , _source_row_number
        , _source_updated_at
    from cte_stg__jsr__lv
    where lv_name is not null
    qualify row_number() over (partition by lv_name order by lv_variant nulls first, _source_row_number) = 1
)

, cte_lv_manufacturer_parts as ( -- 'NPO-E/KBKhA' -> one row per part, across every variant
    select
        lv_name
        , rtrim(trim(p.part), '?') as org_code
    from cte_stg__jsr__lv
    cross join unnest(string_split(lv_manufacturer_code, '/')) with ordinality as p(part, ord)
    where lv_name is not null and lv_manufacturer_code is not null and rtrim(trim(p.part), '?') <> ''
)

, cte_lv_manufacturer_codes as ( -- one row per launch vehicle name and manufacturer code
    select distinct
        lv_name
        , org_code
    from cte_lv_manufacturer_parts
)

, cte_lv_manufacturer_lists as (
    select
        m.lv_name
        , list(m.org_code order by m.org_code) as lv_manufacturer_codes
        , list(coalesce(o.org_display_name, m.org_code) order by m.org_code) as lv_manufacturer_names
    from cte_lv_manufacturer_codes as m
    left join cte_int__jsr__org_organisations as o using (org_code)
    group by m.lv_name
)

, cte_final as (
    select
        r.lv_name
        , {{ helper__derive_lv_brand('r.lv_name') }} as lv_brand
        , r.lv_family
        , r.lv_generic_name
        , case when r.lv_class in ('D', 'M', 'O', 'R', 'V', 'X', 'Y', 'A', 'C', 'Q', 'T', 'W') then r.lv_class end as lv_class
        , coalesce(m.lv_manufacturer_codes, cast([] as varchar[])) as lv_manufacturer_codes
        , coalesce(m.lv_manufacturer_names, cast([] as varchar[])) as lv_manufacturer_names
        , r.lv_variant
        , r.lv_alias
        , r.lv_length_m
        , r.lv_diameter_m
        , r.lv_launch_mass_t
        , r.lv_leo_capacity_kg
        , r.lv_gto_capacity_kg
        , r.lv_takeoff_thrust_kn
        , r._source_updated_at
        , {{ helper__audit_fields() }}
    from cte_lv_preferred_variant as r
    left join cte_lv_manufacturer_lists as m using (lv_name)
)

select * from cte_final
