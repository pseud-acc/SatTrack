-- Parity check: SQL helper__derive_lv_brand() vs the Python prototype (phase 0). Run with dbt show / compile.
select distinct launch_vehicle_name, {{ helper__derive_lv_brand('launch_vehicle_name') }} as launch_vehicle_brand
from {{ ref('stg__jsr__lv') }}
where launch_vehicle_name is not null
