-- One row per launch vehicle name, with its brand, family, class, manufacturers and performance figures.
with cte_int__jsr__launch_vehicles as (
    select
        lv_name
        , lv_brand
        , lv_family
        , lv_generic_name
        , lv_class
        , lv_manufacturer_codes
        , lv_manufacturer_names
        , lv_variant
        , lv_alias
        , lv_length_m
        , lv_diameter_m
        , lv_launch_mass_t
        , lv_leo_capacity_kg
        , lv_gto_capacity_kg
        , lv_takeoff_thrust_kn
        , _source_updated_at
    from {{ ref('int__jsr__launch_vehicles') }}
)

, cte_final as (
    select
        cast(lv_name as varchar) as lv_name
        , cast(lv_brand as varchar) as lv_brand
        , cast(lv_family as varchar) as lv_family
        , cast(lv_generic_name as varchar) as lv_generic_name
        , cast(lv_class as varchar) as lv_class
        , cast(lv_manufacturer_codes as varchar[]) as lv_manufacturer_codes
        , cast(lv_manufacturer_names as varchar[]) as lv_manufacturer_names
        , cast(lv_variant as varchar) as lv_variant
        , cast(lv_alias as varchar) as lv_alias
        , cast(lv_length_m as double) as lv_length_m
        , cast(lv_diameter_m as double) as lv_diameter_m
        , cast(lv_launch_mass_t as double) as lv_launch_mass_t
        , cast(lv_leo_capacity_kg as double) as lv_leo_capacity_kg
        , cast(lv_gto_capacity_kg as double) as lv_gto_capacity_kg
        , cast(lv_takeoff_thrust_kn as double) as lv_takeoff_thrust_kn
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_int__jsr__launch_vehicles
)

select * from cte_final
