{#- D-046: 1 when a CelesTrak constellation member's name fits its group, else 0. Every exception to the name check
    lives here, one `when` each, with the reason and the trigger that removes it (owner, 24 Nov 2026):
      * dmc: not checked. CelesTrak's "Disaster Monitoring" group lists satellites of several programmes (BEIJING 1,
        HUANJING 1A/1B, YAOGAN-4, DEIMOS-1 beside UK-DMC 2 and DMC3); the owner keeps CelesTrak's membership.
        Remove if CelesTrak narrows the group to DMC-named satellites.
      * hulianwang: names starting GUOWANG fit too (GUOWANG-30 OBJECT A..J on 22 Nov 2026). Remove when Space-Track
        renames those objects.
    Otherwise the name must contain the expected string (the group's prefix, else its most common leading word). -#}
{% macro helper__flag_member_name_fits_group(celestrak_group, object_name, expected_name_string) -%}
case
    when {{ celestrak_group }} = 'dmc'
        then 1
    when {{ celestrak_group }} = 'hulianwang' and starts_with(upper({{ object_name }}), 'GUOWANG')
        then 1
    when strpos(upper(coalesce({{ object_name }}, '')), upper({{ expected_name_string }})) > 0
        then 1
    else 0
end
{%- endmacro %}
