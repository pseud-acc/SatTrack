{#- The live app's 5-class orbit rule (SatTrack app export_app_data.py), ported 2026-10-25.
    LEO: period < 128 min and e < 0.25; GEO: mean motion 0.99-1.01 rev/day, e < 0.01, i < 1 deg;
    GSO: period within 0.97-1.03 x 1436 min; MEO: 128 min <= period < 0.97 x 1436; else HEO. -#}
{% macro helper__classify_orbit_class(period, ecc, mean_motion, inc) -%}
(case
    when {{ period }} is null then null
    when {{ period }} < 128 and {{ ecc }} < 0.25 then 'LEO'
    when {{ mean_motion }} between 0.99 and 1.01 and {{ ecc }} < 0.01 and {{ inc }} < 1 then 'GEO'
    when {{ period }} between 1436 * 0.97 and 1436 * 1.03 then 'GSO'
    when {{ period }} >= 128 and {{ period }} < 1436 * 0.97 then 'MEO'
    else 'HEO'
end)
{%- endmacro %}
