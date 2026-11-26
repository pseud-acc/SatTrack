{#- D-046, D-047: 1 when a CelesTrak group member's name fits its group, else 0. System groups keep only members that
    fit (D-047 exclusion); for constellation groups a misfit is a warning. Every exception to the name check lives
    here, one `when` each, with the reason and the trigger that removes it:
      * hulianwang: names starting GUOWANG fit too (GUOWANG-30 OBJECT A..J on 22 Nov 2026). Remove when Space-Track
        renames those objects.
    (D-047 removed D-046's dmc exception: SSTL's list of DMC satellites and GCAT's DMC programme both leave out
    BEIJING 1's neighbours in CelesTrak's dmc group, HJ-1A/1B and YAOGAN-4, so the check now applies to dmc; GCAT
    then adds BEIJING 1 and DEIMOS 1 back through the DMC programme.)
    Otherwise the name must contain the expected string (the group's prefix, else its most common leading word). -#}
{% macro helper__flag_member_name_fits_group(celestrak_group, object_name, expected_name_string) -%}
case
    when {{ celestrak_group }} = 'hulianwang' and starts_with(upper({{ object_name }}), 'GUOWANG')
        then 1
    when strpos(upper(coalesce({{ object_name }}, '')), upper({{ expected_name_string }})) > 0
        then 1
    else 0
end
{%- endmacro %}
