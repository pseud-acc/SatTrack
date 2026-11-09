-- Parity check: SQL helper__derive_lv_brand() vs the Python prototype (phase 0). Run with dbt show / compile.
select distinct lv_name, {{ helper__derive_lv_brand('lv_name') }} as lv_brand
from {{ ref('stg__jsr__lv') }}
where lv_name is not null
