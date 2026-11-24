{% docs src__spacetrack %}
Space-Track.org, the USSPACECOM outlet for unclassified space domain awareness data. SatTrack uses the **GP class**: "an efficient listing of the newest SGP4 keplerian element set for each man-made earth-orbiting object tracked by the 18th Space Defense Squadron" ([Space-Track documentation](https://www.space-track.org/documentation)), and the **boxscore** class for country-code meanings.
{% enddocs %}

{% docs tbl__spacetrack__gp %}
Newest GP element set per on-orbit object (query `decay_date/null-val/epoch/>now-10`), in CCSDS OMM keywords ([CCSDS 502.0-B-3](https://public.ccsds.org/Pubs/502x0b3e1.pdf)). One row per `NORAD_CAT_ID`.
{% enddocs %}

{% docs src__jsr %}
GCAT, the General Catalog of Artificial Space Objects by Jonathan C. McDowell ([planet4589.org/space/gcat](https://planet4589.org/space/gcat/)). Public TSV files; each carries its data update time in a `# Updated` row.
{% enddocs %}

{% docs tbl__jsr__satcat %}
GCAT object catalog. Column meanings: [Object Catalog Column Descriptions](https://planet4589.org/space/gcat/web/cat/cols.html).
{% enddocs %}

{% docs tbl__jsr__psatcat %}
GCAT payload catalog. Column meanings: [Payload Catalog Column Descriptions](https://planet4589.org/space/gcat/web/cat/pcols.html).
{% enddocs %}


{% docs src__celestrak %}
CelesTrak (Dr T.S. Kelso, [celestrak.org](https://celestrak.org/)). SatTrack takes only its **GP group lists** for the constellation and operator groups named in the pipeline's config (D-026), downloaded by the pipeline on GitHub's runners under CelesTrak's [usage policy](https://celestrak.org/usage-policy.php) (D-008). Credit: "Constellation groups: CelesTrak (Dr T.S. Kelso)".
{% enddocs %}

{% docs tbl__celestrak__gp_group_member %}
One row per object per configured CelesTrak group: the group's CSV ([GP data formats](https://celestrak.org/NORAD/documentation/gp-data-formats.php), `gp.php?GROUP=<group>&FORMAT=csv`) unchanged, with the group name in front (`GROUP`). Replaced only when every configured group downloads; otherwise the last good copy stays.
{% enddocs %}

{% docs tbl__celestrak__gp_group_index %}
Every group linked from CelesTrak's [GP index page](https://celestrak.org/NORAD/elements/), with its title and position on the page, parsed at ingestion (`sattrack_ingest/celestrak.py`). Used for display names and to warn about groups the config doesn't know.
{% enddocs %}

{% docs tbl__celestrak__group_config %}
The pipeline's CelesTrak group list (`sattrack_ingest/config.py`, D-026): included constellation and operator groups in precedence order, and the excluded groups. Landed every run; not downloaded.
{% enddocs %}
