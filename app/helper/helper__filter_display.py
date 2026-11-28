"""
What the filter panel shows about its own values (roadmap 3.3b, D-044): the live match count, the "matching / total"
next to each type switch, the hint when a switched-on type matches nothing, the active-filter chips and the summaries
on the "More filters" rows.

Everything comes from the panel's control values, through the same builder as the filter-spec store
(helper__app_data.sidebar_filter_spec), so the count is the store's spec run on the server (Q4). The page renders
panel_summary() for the starting values, and a callback renders it again after each change.

Functions:
    default_controls: the values the tracker opens with (D-049), which "Clear all" restores
    widened_controls: the value a chip's remove button sets, per chip
    panel_summary: count, type counts, hints, chips and row summaries for a set of control values
"""

from app.core import filter_spec
from app.helper.helper__app_data import (sidebar_filter_spec, type_matches, OBJECT_TYPES, DEFAULT_STATUS,
                                         DEFAULT_ORBITS, DEFAULT_TYPES, launch_year_bounds)

TYPE_LABELS = {"PAYLOAD": "Payloads", "ROCKET BODY": "Rocket bodies", "DEBRIS": "Debris"}

# The panel's controls, in sidebar_filter_spec's argument order, with the id of each (its `value` property).
CONTROLS = {
    "status": "status-filter-checkbox",
    "orbit": "orbit-filter-checkbox",
    "satname": "satname-filter-dropdown",
    "satcatid": "satcatid-filter-dropdown",
    "owner": "owner-filter-multi-dropdown",
    "launchvehicle": "launchvehicle-filter-multi-dropdown",
    "purpose": "purpose-filter-multi-dropdown",
    "year": "launchyear-filter-slider",
    "types": "type-filter-checkbox",
    # Constellations and satellite systems (roadmap 3.14, D-047); the switch narrows the system filter to the
    # system each object was built for
    "constellation": "constellation-filter-multi-dropdown",
    "system": "system-filter-multi-dropdown",
    "systemprimary": "system-primary-switch",
}

# Chips, in the order they show. The type chip has no remove button: the switches right above it set the types.
CHIPS = ["types", "status", "orbit", "satname", "satcatid", "owner", "launchvehicle", "purpose", "constellation",
         "system", "year"]
REMOVABLE_CHIPS = [c for c in CHIPS if c != "types"]

# The "More filters" rows: control -> the filter-spec field whose label (D-030) the row shows.
ROWS = {"constellation": "satellite_constellation_name", "system": "satellite_system_names", "owner": "owner_country",
        "launchvehicle": "launch_vehicle_brand", "purpose": "mission_category_labels", "year": "launch_year"}


def default_controls():
    """The values the tracker opens with (owner, 26 Nov 2026; D-049). "Clear all" goes back to these."""
    return {"status": DEFAULT_STATUS, "orbit": list(DEFAULT_ORBITS), "satname": None, "satcatid": None, "owner": [],
            "launchvehicle": [], "purpose": [], "year": launch_year_bounds(), "types": list(DEFAULT_TYPES),
            "constellation": [], "system": [], "systemprimary": False}


def widened_controls():
    """Per removable chip, the value its remove button gives the control: the value that filters nothing out (status
    All, every orbit class, the whole year range, nothing selected), not the default, so removing "Active" shows
    Inactive too."""
    return {"status": "All", "orbit": list(DEFAULT_ORBITS), "satname": None, "satcatid": None, "owner": [],
            "launchvehicle": [], "purpose": [], "year": launch_year_bounds(), "constellation": [], "system": []}


def _picked(values):
    """'Any' for nothing picked, the value for one, 'first +N' for more."""
    values = list(values or [])
    if not values:
        return "Any"
    return values[0] if len(values) == 1 else f"{values[0]} +{len(values) - 1}"


def _years(year):
    lo, hi = launch_year_bounds()
    if year is None or (int(year[0]) <= lo and int(year[1]) >= hi):
        return None
    return f"{int(year[0])}–{int(year[1])}"


def _chips(c, name_of=lambda satcat_id: None):
    """Chip text per chip (None: no chip). Prefixes are the fields' labels from the schema (D-030). A picked
    satellite's chip shows its name too (`name_of`: SATCAT number -> object name, or None)."""
    lbl = filter_spec.label
    types = [TYPE_LABELS[t] for t in OBJECT_TYPES if t in (c["types"] or [])]
    orbit = [o for o in DEFAULT_ORBITS if o in (c["orbit"] or [])]
    years = _years(c["year"])
    return {
        "types": ", ".join(types) if types else "No object type",
        "status": None if c["status"] == "All" else (c["status"] or "No status"),
        "orbit": None if orbit == list(DEFAULT_ORBITS) else f"{lbl('orbit_class')}: {', '.join(orbit) or 'none'}",
        "satname": None if c["satname"] is None else f"{lbl('object_name')}: {c['satname']}",
        "satcatid": None if c["satcatid"] is None else (
            f"{name_of(c['satcatid'])} ({lbl('satcat_id')} {c['satcatid']})" if name_of(c["satcatid"])
            else f"{lbl('satcat_id')}: {c['satcatid']}"),
        "owner": f"{lbl('owner_country')}: {_picked(c['owner'])}" if c["owner"] else None,
        "launchvehicle": f"{lbl('launch_vehicle_brand')}: {_picked(c['launchvehicle'])}" if c["launchvehicle"] else None,
        "purpose": f"{lbl('mission_category_labels')}: {_picked(c['purpose'])}" if c["purpose"] else None,
        "constellation": (f"{lbl('satellite_constellation_name')}: {_picked(c['constellation'])}"
                          if c["constellation"] else None),
        # the label says which field filters: every system, or the primary one only
        "system": (f"{lbl('primary_satellite_system_name' if c['systemprimary'] else 'satellite_system_names')}: "
                   f"{_picked(c['system'])}" if c["system"] else None),
        "year": None if years is None else f"{lbl('launch_year')}: {years}",
    }


def _hints(c, matches, filter_table):
    """One line per switched-on type that matches nothing (owner, 24 Nov 2026, Q2): saying when status is the
    reason, which it almost always is for rocket bodies and debris (D-049)."""
    zero = [t for t in OBJECT_TYPES if t in (c["types"] or []) and matches[t] == 0]
    if not zero:
        return []
    widened = None
    if c["status"] != "All":
        args = {k: c[k] for k in CONTROLS if k != "types"}
        widened = type_matches(filter_table, sidebar_filter_spec(**{**args, "status": "All"}))
    hints = []
    for t in zero:
        if widened is not None and widened[t] > 0:
            hints.append(f"{TYPE_LABELS[t]}: 0 match, because status is {c['status']}.")
        else:
            hints.append(f"{TYPE_LABELS[t]}: 0 match the other filters.")
    return hints


def _object_name(filter_table, satcat_id):
    """The object's name from the filter table, or None (no such object, no name, or not a number)."""
    try:
        hit = filter_table.loc[filter_table["satcat_id"] == int(satcat_id), "object_name"]
    except (TypeError, ValueError):
        return None
    name = hit.iloc[0] if len(hit) and isinstance(hit.iloc[0], str) else None
    return None if name == "TBA - TO BE ASSIGNED" else name   # Space-Track's "not yet named": the chip shows the number


def panel_summary(filter_table, controls):
    """
    What the panel shows for a set of control values.

    @param filter_table: (DataFrame) the objects dataset's filterable fields (every object, UNKNOWN included)
    @param controls: (dict) control name (CONTROLS) -> value
    @return: (dict) count, total, matches (type -> count), totals (type -> count), hints (list of str),
             chips (chip -> text or None), rows (row -> summary text), changed (bool: differs from the defaults)
    """
    c = {**default_controls(), **controls}
    base = sidebar_filter_spec(**{k: c[k] for k in CONTROLS if k != "types"})
    matches = type_matches(filter_table, base)
    totals = {t: int(n) for t, n in filter_table["object_type"].value_counts().reindex(OBJECT_TYPES, fill_value=0).items()}
    shown = [t for t in OBJECT_TYPES if t in (c["types"] or [])]
    return {
        "count": sum(matches[t] for t in shown),
        "total": len(filter_table),
        "matches": matches,
        "totals": totals,
        "hints": _hints(c, matches, filter_table),
        "chips": _chips(c, lambda i: _object_name(filter_table, i)),
        "rows": {"owner": _picked(c["owner"]), "launchvehicle": _picked(c["launchvehicle"]),
                 "purpose": _picked(c["purpose"]), "constellation": _picked(c["constellation"]),
                 "system": _picked(c["system"]), "year": _years(c["year"]) or "Any"},
        "changed": _normalised(c) != _normalised(default_controls()),
    }


def _normalised(c):
    return {k: (bool(v) if k == "systemprimary" else sorted(v) if isinstance(v, list) and k != "year" else
                [int(y) for y in v] if k == "year" and v is not None else v) for k, v in c.items()}
