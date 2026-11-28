"""The catalogue at a glance (home page and Explore pages; owner's N2 / S1 choices of 28 Nov 2026, D-059).

build_summary() counts what the app's own datasets hold, once at start-up, so every figure on the home page and the
Explore pages is read from the data and never typed in:

- the totals: tracked objects, working satellites (active payloads), inactive satellites, rocket bodies, debris;
- the working satellites grouped six ways (the Explore pages): constellation, satellite system, operator, owner
  country, mission and orbit type, each ranked by its number of working satellites;
- "From SatTrack's records": figures only this catalogue's status, ownership and data-quality fields can give;
- well-known objects present in the data (links that open the tracker with the object selected, D-024).

Pure functions over plain records (the objects dataset's, and object_detail's where published); nothing here reads
files or the app's state. A dataset without object_detail gives no operator ranking and no records strip.
"""
from __future__ import annotations

from collections import Counter

# The Explore views, in the order the menu lists them: key -> (title, the one-line description under it, what one
# entry is called). The descriptions for constellation and system are D-047's.
VIEWS = {
    "constellations": ("Constellations", "Near-identical satellites working together.", "constellation"),
    "systems": ("Satellite systems", "Different satellites working together on one service.", "system"),
    "operators": ("Operators", "The organisations that run the satellites.", "operator"),
    "countries": ("Countries", "Where the satellites' owners are based.", "country"),
    "missions": ("Missions", "What the satellites are for, as GCAT classes them.", "mission"),
    "orbits": ("Orbits", "The kind of path each satellite follows.", "orbit type"),
}

# Well-known objects for the home page's quick links: SATCAT number -> the name to show. Only those present in the
# data are offered (so a link can never lead nowhere).
WELL_KNOWN = {25544: "International Space Station", 20580: "Hubble Space Telescope", 48274: "Tiangong space station"}


def _ranked(counter: Counter) -> list[dict]:
    """[{name, count}] by count, then name, so ties never reorder between runs."""
    return [{"name": name, "count": n} for name, n in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))]


def build_summary(objects: list[dict], details: list[dict] | None = None) -> dict:
    """
    @param objects: the objects dataset's records (every tracked object)
    @param details: object_detail's records, or None when that dataset isn't published
    @return: {"totals": {...}, "views": {key: {"entries": [{name, count}], "groups": n, "satellites": n}},
              "records": {...} or None, "well_known": [{satcat_id, name}]}
    """
    payloads = [r for r in objects if r.get("object_type") == "PAYLOAD"]
    working = [r for r in payloads if r.get("operational_status") == "Active"]
    totals = {
        "tracked": len(objects),
        "working": len(working),
        "inactive": len(payloads) - len(working),
        "rocket_bodies": sum(1 for r in objects if r.get("object_type") == "ROCKET BODY"),
        "debris": sum(1 for r in objects if r.get("object_type") == "DEBRIS"),
    }
    detail_by_id = {d["satcat_id"]: d for d in (details or [])}

    counters = {key: Counter() for key in VIEWS}
    for r in working:
        if r.get("satellite_constellation_name"):
            counters["constellations"][r["satellite_constellation_name"]] += 1
        for system in r.get("satellite_system_names") or []:
            counters["systems"][system] += 1
        if r.get("owner_country"):
            counters["countries"][r["owner_country"]] += 1
        for mission in r.get("mission_category_labels") or []:
            counters["missions"][mission] += 1
        if r.get("orbit_class"):
            counters["orbits"][r["orbit_class"]] += 1
        operator = (detail_by_id.get(r["satcat_id"]) or {}).get("operator_name")
        if operator:
            counters["operators"][operator] += 1
    views = {}
    for key, counter in counters.items():
        entries = _ranked(counter)
        # satellites: working satellites with a value in this view (a satellite in two systems counts once)
        views[key] = {"entries": entries, "groups": len(entries), "satellites": _members(working, detail_by_id, key)}

    records = None
    if details:
        records = {
            "still_transmitting": sum(1 for d in details
                                      if d.get("flag_still_operating") == 0 and d.get("flag_still_transmitting") == 1),
            "several_owners": sum(1 for d in details if len(d.get("owner_org_names") or []) > 1),
            "estimated_mass": sum(1 for d in details if d.get("flag_mass_estimated") == 1),
            "uncertain_match": sum(1 for d in details if d.get("flag_catalog_match_uncertain") == 1),
        }

    present = {r["satcat_id"] for r in objects}
    well_known = [{"satcat_id": i, "name": name} for i, name in WELL_KNOWN.items() if i in present]
    return {"totals": totals, "views": views, "records": records, "well_known": well_known}


def _members(working: list[dict], detail_by_id: dict, key: str) -> int:
    def has(r):
        if key == "constellations":
            return bool(r.get("satellite_constellation_name"))
        if key == "systems":
            return bool(r.get("satellite_system_names"))
        if key == "countries":
            return bool(r.get("owner_country"))
        if key == "missions":
            return bool(r.get("mission_category_labels"))
        if key == "orbits":
            return bool(r.get("orbit_class"))
        return bool((detail_by_id.get(r["satcat_id"]) or {}).get("operator_name"))
    return sum(1 for r in working if has(r))
