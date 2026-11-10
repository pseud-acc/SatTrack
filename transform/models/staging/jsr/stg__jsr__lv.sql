-- 1:1 with raw_jsr.lv: rename + cast only. Unique on (launch_vehicle_name, launch_vehicle_variant).
with cte_final as (
    select
        {{ helper__clean_gcat_text('LV_Name') }} as launch_vehicle_name
        , {{ helper__clean_gcat_text('LV_Family') }} as launch_vehicle_family
        , {{ helper__clean_gcat_text('LV_Manufacturer') }} as launch_vehicle_manufacturer_code
        , {{ helper__clean_gcat_text('LV_Variant') }} as launch_vehicle_variant
        , {{ helper__clean_gcat_text('LV_Alias') }} as launch_vehicle_alias
        , {{ helper__clean_gcat_text('LV_Min_Stage') }} as launch_vehicle_min_stage
        , {{ helper__clean_gcat_text('LV_Max_Stage') }} as launch_vehicle_max_stage
        , {{ helper__cast_gcat_value('Length', 'double') }} as launch_vehicle_length_m
        , {{ helper__clean_gcat_text('LFlag') }} as launch_vehicle_length_flag
        , {{ helper__cast_gcat_value('Diameter', 'double') }} as launch_vehicle_diameter_m
        , {{ helper__clean_gcat_text('DFlag') }} as launch_vehicle_diameter_flag
        , {{ helper__cast_gcat_value('Launch_Mass', 'double') }} as launch_vehicle_launch_mass_t
        , {{ helper__clean_gcat_text('MFlag') }} as launch_vehicle_launch_mass_flag
        , {{ helper__cast_gcat_value('LEO_Capacity', 'double') }} as launch_vehicle_leo_capacity_kg
        , {{ helper__cast_gcat_value('GTO_Capacity', 'double') }} as launch_vehicle_gto_capacity_kg
        , {{ helper__cast_gcat_value('TO_Thrust', 'double') }} as launch_vehicle_takeoff_thrust_kn
        , {{ helper__clean_gcat_text('Class') }} as launch_vehicle_class
        , {{ helper__cast_gcat_value('Apogee', 'double') }} as launch_vehicle_max_apogee_km
        , {{ helper__cast_gcat_value('Range', 'double') }} as launch_vehicle_range_km
        , {{ helper__clean_gcat_text('GenericName') }} as launch_vehicle_generic_name
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _run_id
    from {{ source('jsr', 'lv') }}
)

select * from cte_final
