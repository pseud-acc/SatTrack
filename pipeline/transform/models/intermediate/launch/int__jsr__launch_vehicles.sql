-- One row per launch vehicle name (the launch log joins on name only). GCAT's own key is name + variant;
-- the row without a variant is preferred, then the first variant. Manufacturers from every variant are
-- kept as a list (no manual override, plan section 15.1). Undocumented class values (e.g. 'B') become NULL.
with cte_stg__jsr__lv as (
    select
        launch_vehicle_name
        , launch_vehicle_family
        , launch_vehicle_generic_name
        , launch_vehicle_class
        , launch_vehicle_manufacturer_code
        , launch_vehicle_variant
        , launch_vehicle_alias
        , launch_vehicle_length_m
        , launch_vehicle_diameter_m
        , launch_vehicle_launch_mass_t
        , launch_vehicle_leo_capacity_kg
        , launch_vehicle_gto_capacity_kg
        , launch_vehicle_takeoff_thrust_kn
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

, cte_launch_vehicle_preferred_variant as ( -- one row per name: no-variant row first, then the first variant
    select
        launch_vehicle_name
        , launch_vehicle_family
        , launch_vehicle_generic_name
        , launch_vehicle_class
        , launch_vehicle_manufacturer_code
        , launch_vehicle_variant
        , launch_vehicle_alias
        , launch_vehicle_length_m
        , launch_vehicle_diameter_m
        , launch_vehicle_launch_mass_t
        , launch_vehicle_leo_capacity_kg
        , launch_vehicle_gto_capacity_kg
        , launch_vehicle_takeoff_thrust_kn
        , _source_row_number
        , _source_updated_at
    from cte_stg__jsr__lv
    where launch_vehicle_name is not null
    qualify row_number() over (partition by launch_vehicle_name order by launch_vehicle_variant nulls first, _source_row_number) = 1
)

, cte_launch_vehicle_manufacturer_parts as ( -- 'NPO-E/KBKhA' -> one row per part, across every variant
    select
        launch_vehicle_name
        , rtrim(trim(p.part), '?') as org_code
    from cte_stg__jsr__lv
    cross join unnest(string_split(launch_vehicle_manufacturer_code, '/')) with ordinality as p(part, ord)
    where launch_vehicle_name is not null and launch_vehicle_manufacturer_code is not null and rtrim(trim(p.part), '?') <> ''
)

, cte_launch_vehicle_manufacturer_codes as ( -- one row per launch vehicle name and manufacturer code
    select distinct
        launch_vehicle_name
        , org_code
    from cte_launch_vehicle_manufacturer_parts
)

, cte_launch_vehicle_manufacturer_lists as (
    select
        m.launch_vehicle_name
        , list(m.org_code order by m.org_code) as launch_vehicle_manufacturer_codes
        , list(coalesce(o.org_display_name, m.org_code) order by m.org_code) as launch_vehicle_manufacturer_names
    from cte_launch_vehicle_manufacturer_codes as m
    left join cte_int__jsr__org_organisations as o using (org_code)
    group by m.launch_vehicle_name
)

, cte_final as (
    select
        r.launch_vehicle_name
        , {{ helper__derive_lv_brand('r.launch_vehicle_name') }} as launch_vehicle_brand
        , r.launch_vehicle_family
        , r.launch_vehicle_generic_name
        , case when r.launch_vehicle_class in ('D', 'M', 'O', 'R', 'V', 'X', 'Y', 'A', 'C', 'Q', 'T', 'W') then r.launch_vehicle_class end as launch_vehicle_class
        , coalesce(m.launch_vehicle_manufacturer_codes, cast([] as varchar[])) as launch_vehicle_manufacturer_codes
        , coalesce(m.launch_vehicle_manufacturer_names, cast([] as varchar[])) as launch_vehicle_manufacturer_names
        , r.launch_vehicle_variant
        , r.launch_vehicle_alias
        , r.launch_vehicle_length_m
        , r.launch_vehicle_diameter_m
        , r.launch_vehicle_launch_mass_t
        , r.launch_vehicle_leo_capacity_kg
        , r.launch_vehicle_gto_capacity_kg
        , r.launch_vehicle_takeoff_thrust_kn
        , r._source_updated_at
        , {{ helper__audit_fields() }}
    from cte_launch_vehicle_preferred_variant as r
    left join cte_launch_vehicle_manufacturer_lists as m using (launch_vehicle_name)
)

select * from cte_final
