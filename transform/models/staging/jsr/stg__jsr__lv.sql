-- 1:1 with raw_jsr.lv: rename + cast only. Unique on (lv_name, lv_variant).
with cte_final as (
    select
        {{ helper__clean_gcat_text('LV_Name') }} as lv_name
        , {{ helper__clean_gcat_text('LV_Family') }} as lv_family
        , {{ helper__clean_gcat_text('LV_Manufacturer') }} as lv_manufacturer_code
        , {{ helper__clean_gcat_text('LV_Variant') }} as lv_variant
        , {{ helper__clean_gcat_text('LV_Alias') }} as lv_alias
        , {{ helper__clean_gcat_text('LV_Min_Stage') }} as lv_min_stage
        , {{ helper__clean_gcat_text('LV_Max_Stage') }} as lv_max_stage
        , {{ helper__cast_gcat_value('Length', 'double') }} as lv_length_m
        , {{ helper__clean_gcat_text('LFlag') }} as lv_length_flag
        , {{ helper__cast_gcat_value('Diameter', 'double') }} as lv_diameter_m
        , {{ helper__clean_gcat_text('DFlag') }} as lv_diameter_flag
        , {{ helper__cast_gcat_value('Launch_Mass', 'double') }} as lv_launch_mass_t
        , {{ helper__clean_gcat_text('MFlag') }} as lv_launch_mass_flag
        , {{ helper__cast_gcat_value('LEO_Capacity', 'double') }} as lv_leo_capacity_kg
        , {{ helper__cast_gcat_value('GTO_Capacity', 'double') }} as lv_gto_capacity_kg
        , {{ helper__cast_gcat_value('TO_Thrust', 'double') }} as lv_takeoff_thrust_kn
        , {{ helper__clean_gcat_text('Class') }} as lv_class
        , {{ helper__cast_gcat_value('Apogee', 'double') }} as lv_max_apogee_km
        , {{ helper__cast_gcat_value('Range', 'double') }} as lv_range_km
        , {{ helper__clean_gcat_text('GenericName') }} as lv_generic_name
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _run_id
    from {{ source('jsr', 'lv') }}
)

select * from cte_final
