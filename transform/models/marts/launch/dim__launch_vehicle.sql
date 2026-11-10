-- One row per launch vehicle name, with its brand, family, class, manufacturers and performance figures.
with cte_int__jsr__launch_vehicles as (
    select
        launch_vehicle_name
        , launch_vehicle_brand
        , launch_vehicle_family
        , launch_vehicle_generic_name
        , launch_vehicle_class
        , launch_vehicle_manufacturer_codes
        , launch_vehicle_manufacturer_names
        , launch_vehicle_variant
        , launch_vehicle_alias
        , launch_vehicle_length_m
        , launch_vehicle_diameter_m
        , launch_vehicle_launch_mass_t
        , launch_vehicle_leo_capacity_kg
        , launch_vehicle_gto_capacity_kg
        , launch_vehicle_takeoff_thrust_kn
        , _source_updated_at
    from {{ ref('int__jsr__launch_vehicles') }}
)

, cte_final as (
    select
        cast(launch_vehicle_name as varchar) as launch_vehicle_name
        , cast(launch_vehicle_brand as varchar) as launch_vehicle_brand
        , cast(launch_vehicle_family as varchar) as launch_vehicle_family
        , cast(launch_vehicle_generic_name as varchar) as launch_vehicle_generic_name
        , cast(launch_vehicle_class as varchar) as launch_vehicle_class
        , cast(launch_vehicle_manufacturer_codes as varchar[]) as launch_vehicle_manufacturer_codes
        , cast(launch_vehicle_manufacturer_names as varchar[]) as launch_vehicle_manufacturer_names
        , cast(launch_vehicle_variant as varchar) as launch_vehicle_variant
        , cast(launch_vehicle_alias as varchar) as launch_vehicle_alias
        , cast(launch_vehicle_length_m as double) as launch_vehicle_length_m
        , cast(launch_vehicle_diameter_m as double) as launch_vehicle_diameter_m
        , cast(launch_vehicle_launch_mass_t as double) as launch_vehicle_launch_mass_t
        , cast(launch_vehicle_leo_capacity_kg as double) as launch_vehicle_leo_capacity_kg
        , cast(launch_vehicle_gto_capacity_kg as double) as launch_vehicle_gto_capacity_kg
        , cast(launch_vehicle_takeoff_thrust_kn as double) as launch_vehicle_takeoff_thrust_kn
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_int__jsr__launch_vehicles
)

select * from cte_final
