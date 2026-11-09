-- Data quality tab: share of objects with a value in each key app field, by object type.
with cte_fct__satellite_master as (
    select
        object_type
        , status
        , launch_date
        , owner_country
        , operator_name
        , manufacturer_name
        , site_name
        , lv_brand
        , satellite_program
        , orbit_class
        , rcs_size
        , mass_kg
        , mission_category_labels
    from {{ ref('fct__satellite_master') }}
)

, cte_field_values as (
    select
        object_type
        , f.field.name as field
        , f.field.filled as filled
    from cte_fct__satellite_master
    cross join unnest([
        {'name': 'status', 'filled': status is not null}
        , {'name': 'launch_date', 'filled': launch_date is not null}
        , {'name': 'owner_country', 'filled': owner_country is not null}
        , {'name': 'operator_name', 'filled': operator_name is not null}
        , {'name': 'manufacturer_name', 'filled': manufacturer_name is not null}
        , {'name': 'site_name', 'filled': site_name is not null}
        , {'name': 'lv_brand', 'filled': lv_brand is not null}
        , {'name': 'satellite_program', 'filled': satellite_program is not null}
        , {'name': 'orbit_class', 'filled': orbit_class is not null}
        , {'name': 'rcs_size', 'filled': rcs_size is not null}
        , {'name': 'mass_kg', 'filled': mass_kg is not null}
        , {'name': 'mission_category_labels', 'filled': len(mission_category_labels) > 0}
    ]) as f(field)
)

, cte_final as (
    select
        field
        , object_type
        , avg(cast(coalesce(filled, false) as integer)) as fill_rate
    from cte_field_values
    group by
        field
        , object_type
)

select * from cte_final
