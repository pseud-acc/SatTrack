-- 1:1 with raw_jsr.currentcat: rename + cast only.
with cte_final as (
    select
        {{ helper__clean_gcat_text('JCAT') }} as jcat
        , {{ helper__clean_gcat_text('DeepCat') }} as deepcat_jcat
        , {{ helper__clean_gcat_text('Satcat') }} as satcat_ref
        , {{ helper__clean_gcat_text('Piece') }} as cospar_id
        , {{ helper__clean_gcat_text('Active') }} as activity_type
        , {{ helper__clean_gcat_text('Type') }} as sat_type
        , {{ helper__clean_gcat_text('Name') }} as gcat_name
        , {{ helper__clean_gcat_text('LDate') }} as gcat_launch_date_raw
        , {{ helper__clean_gcat_text('Parent') }} as parent_ref
        , {{ helper__clean_gcat_text('Owner') }} as current_owner_code
        , {{ helper__clean_gcat_text('State') }} as current_owner_state_code
        , {{ helper__clean_gcat_text('SDate') }} as first_separation_date_raw
        , {{ helper__clean_gcat_text('ExpandedStatus') }} as current_status
        , {{ helper__clean_gcat_text('DDate') }} as descent_date_raw
        , {{ helper__clean_gcat_text('ODate') }} as current_orbit_epoch_raw
        , {{ helper__cast_gcat_value('Period', 'double') }} as current_period_min
        , {{ helper__cast_gcat_value('Perigee', 'double') }} as current_perigee_km
        , {{ helper__clean_gcat_text('PF') }} as current_perigee_flag
        , {{ helper__cast_gcat_value('Apogee', 'double') }} as current_apogee_km
        , {{ helper__clean_gcat_text('AF') }} as current_apogee_flag
        , {{ helper__cast_gcat_value('Inc', 'double') }} as current_inclination_deg
        , {{ helper__clean_gcat_text('IF') }} as current_inclination_flag
        , {{ helper__clean_gcat_text('OpOrbit') }} as current_orbit_type_raw
        , cast(_loaded_at as timestamp) as _loaded_at
        , cast(_source_updated_at as timestamp) as _source_updated_at
        , cast(_source_row_number as integer) as _source_row_number
        , _run_id
    from {{ source('jsr', 'currentcat') }}
)

select * from cte_final
