"""Helpers shared by the app tests: the sample's reference time, independent expected results, and a caller
that runs a Dash callback the way the browser does.

Expected results here are computed from the sample with plain pandas and the sgp4 library, never with the
app's own helpers, so a test compares the app against an independent statement of what it should do.
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly
from sgp4 import omm
from sgp4.api import Satrec, jday

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DATA_DIR = REPO_ROOT / "tests" / "app_data"

# The status control picks one of Active / Inactive / All (roadmap 3.3b); the CSV statuses each keeps, written out
# here rather than taken from the app.
STATUS_KEEPS = {"Active": ["Active"], "Inactive": ["Inactive"], "All": ["Active", "Inactive"]}
ALL_STATUS = "All"
ALL_ORBITS = ["LEO", "MEO", "GEO", "GSO", "HEO"]
EARTH_RADIUS_KM = 6378.137  # WGS 84 equatorial radius, the value the app uses
MU_EARTH = 398600.4418      # km^3/s^2 (WGS 84)


def load_sample():
    return pd.read_csv(APP_DATA_DIR / "satcat_tle.csv")


def objects_sample_ids():
    """satcat_ids in the sample's objects dataset, read directly (gzip + json), not through the app. The sidebar
    filters on that dataset (D-035), so a CSV satellite missing from it is never shown: 2 of the 341, which
    decayed between the CSV's run and the dataset's."""
    import gzip
    doc = json.loads(gzip.decompress((APP_DATA_DIR / "objects.json.gz").read_bytes()))
    return {r["satcat_id"] for r in doc["records"]}


def objects_sample():
    """The sample's objects dataset (every type) as a DataFrame, read directly (gzip + json), not through the app."""
    import gzip
    doc = json.loads(gzip.decompress((APP_DATA_DIR / "objects.json.gz").read_bytes()))
    return pd.DataFrame.from_records(doc["records"])


def expected_object_count(objects, status="Active", orbit=ALL_ORBITS, types=("PAYLOAD",), year=None):
    """Objects the panel should count (roadmap 3.3b), with plain pandas over the objects dataset: the type is one of
    `types`; status is the control's choice, where Inactive also covers a missing status; orbit class any of; launch
    year inclusive (a missing year is outside any range)."""
    st = objects["operational_status"]
    keeps = STATUS_KEEPS.get(status, [])
    keep = st.isin(keeps) | (st.isna() & ("Inactive" in keeps))
    keep &= objects["object_type"].isin(list(types)) & objects["orbit_class"].isin(orbit)
    if year is not None:
        keep &= objects["launch_year"].between(year[0], year[1])
    return int(keep.sum())


def reference_time():
    """The sample's Space-Track download time (last_data_update.csv). Propagating to a fixed time near the
    element epochs keeps every result independent of the day the tests run and of when the sample was cut."""
    meta = pd.read_csv(APP_DATA_DIR / "last_data_update.csv")
    value = meta.loc[meta["Source"] == "SpaceTrack_GP", "Last Update"].iloc[0]
    return datetime.strptime(value, "%d/%m/%Y, %H:%M:%S")


def frozen_datetime(moment):
    """A datetime class whose utcnow() is `moment`, to replace the app's clock."""
    class Frozen(datetime):
        @classmethod
        def utcnow(cls):
            return moment
    return Frozen


def _teme(sat, when):
    jd, fr = jday(when.year, when.month, when.day, when.hour, when.minute, when.second)
    err, r, _ = sat.sgp4(jd, fr)
    return None if err != 0 else np.array(r)


def sgp4_teme(tle1, tle2, when):
    """Reference position (TEME, km) from TLE lines, with the sgp4 library directly; None on an sgp4 error."""
    return _teme(Satrec.twoline2rv(tle1, tle2), when)


def sgp4_teme_omm(row, when):
    """Reference position (TEME, km) from a satcat_tle.csv row's OMM columns, with the sgp4 library directly
    (sgp4.omm.initialize and the CCSDS OMM keywords); None on an sgp4 error."""
    sat = Satrec()
    omm.initialize(sat, {
        "EPOCH": row["Epoch"], "MEAN_MOTION": row["MeanMotion"], "ECCENTRICITY": row["Eccentricity"],
        "INCLINATION": row["Inclination"], "RA_OF_ASC_NODE": row["RaOfAscNode"],
        "ARG_OF_PERICENTER": row["ArgOfPericenter"], "MEAN_ANOMALY": row["MeanAnomaly"], "BSTAR": row["Bstar"],
        "MEAN_MOTION_DOT": row["MeanMotionDot"], "MEAN_MOTION_DDOT": row["MeanMotionDdot"],
        "REV_AT_EPOCH": row["RevAtEpoch"], "ELEMENT_SET_NO": row["ElementSetNo"],
        "EPHEMERIS_TYPE": row["EphemerisType"], "CLASSIFICATION_TYPE": row["ClassificationType"],
        "OBJECT_ID": row["ObjectId"], "NORAD_CAT_ID": row["SatCatId"]})
    return _teme(sat, when)


def propagates(df, when):
    """Boolean mask: rows sgp4 can propagate to `when` from their OMM fields."""
    return np.array([sgp4_teme_omm(row, when) is not None for _, row in df.iterrows()])


def expected_ids(df, when, status=ALL_STATUS, orbit=ALL_ORBITS, satname=None, satcatid=None, owner=(),
                 launchvehicle=(), purpose=(), year=None):
    """SatCatIds the sidebar should show: the documented filter rules applied with pandas, then only the rows
    that propagate. Rules: status is the control's choice (All keeps both); orbit class is 'any of'; name and catalogue id are exact; owner, launch
    vehicle and purpose filter only when something is selected; purpose matches any part of a '/'-joined value; only satellites in the objects dataset can be shown;
    launch year is an inclusive range."""
    keep = df["Status"].isin(STATUS_KEEPS.get(status, [])) & df["OrbitClass"].isin(orbit)
    if satname is not None:
        keep &= df["ObjectName"] == satname
    if satcatid is not None:
        keep &= df["SatCatId"] == int(satcatid)
    if owner:
        keep &= df["Owner"].isin(owner)
    if launchvehicle:
        keep &= df["LaunchVehicleClass"].isin(launchvehicle)
    if purpose:
        keep &= df["Purpose"].str.split("/").apply(lambda parts: bool(set(parts) & set(purpose)))
    if year is not None:
        keep &= df["LaunchYear"].between(year[0], year[1])
    keep &= df["SatCatId"].isin(objects_sample_ids())   # only objects the filter table knows (D-035)
    keep &= propagates(df, when)
    return set(df.loc[keep, "SatCatId"])


# ---- Dash: callbacks as the browser calls them -------------------------------------------------------------

SIDEBAR = {  # expected_ids() argument -> sidebar component id (its `value` property)
    "status": "status-filter-checkbox",
    "orbit": "orbit-filter-checkbox",
    "satname": "satname-filter-dropdown",
    "satcatid": "satcatid-filter-dropdown",
    "owner": "owner-filter-multi-dropdown",
    "launchvehicle": "launchvehicle-filter-multi-dropdown",
    "purpose": "purpose-filter-multi-dropdown",
    "year": "launchyear-filter-slider",
}


# Every panel control that feeds the filter-spec store (roadmap 3.3a)
PANEL_CONTROLS = set(SIDEBAR.values()) | {"type-filter-checkbox"}


def split_outputs(output):
    """'..a.x...b.y..' or 'a.x' -> [('a', 'x'), ('b', 'y')]; drops an allow_duplicate '@hash' suffix."""
    pairs = [p.rsplit(".", 1) for p in output.strip(".").split("...") if p]
    return [(cid, prop.split("@")[0]) for cid, prop in pairs]


def walk_components(component):
    """Every Dash component in a layout tree, following children and any other prop holding components."""
    stack = [component]
    while stack:
        comp = stack.pop()
        if isinstance(comp, (list, tuple)):
            stack.extend(comp)
            continue
        if not hasattr(comp, "_prop_names"):
            continue
        yield comp
        for name in comp._prop_names:
            value = getattr(comp, name, None)
            if hasattr(value, "_prop_names") or isinstance(value, (list, tuple)):
                stack.append(value)


def layout_by_id(layout):
    return {c.id: c for c in walk_components(layout) if isinstance(getattr(c, "id", None), str)}


class CallbackCaller:
    """POSTs to /_dash-update-component with the page's starting values, overridden per call."""

    def __init__(self, client, dependencies, layout):
        self.client = client
        self.deps = {d["output"]: d for d in dependencies}
        self.components = layout_by_id(layout)

    def find(self, output_id):
        """The callback that sets component `output_id` (any of its outputs)."""
        matches = [d for out, d in self.deps.items() if output_id in {cid for cid, _ in split_outputs(out)}]
        assert len(matches) == 1, f"{len(matches)} callbacks set {output_id}"
        return matches[0]

    def initial(self, cid, prop):
        return getattr(self.components[cid], prop, None)

    def filter_args(self, values):
        """expected_ids() arguments for the sidebar as the page starts (today: Active, LEO + GEO), with any
        'id.prop' in `values` applied, so expectations follow the page's real start state."""
        def v(cid):
            key = f"{cid}.value"
            return values[key] if key in values else self.initial(cid, "value")
        return {name: v(cid) for name, cid in SIDEBAR.items()}

    def spec_for(self, values):
        """The filter spec the page's filter-spec callback makes from `values` (control 'id.value' overrides on the
        starting state), run through /_dash-update-component like any callback (roadmap 3.3a)."""
        changed = next((k for k in values if k.split(".")[0] in PANEL_CONTROLS), None)
        if changed is None:
            return self.initial("filter-spec", "data")
        status, out = self.call("filter-spec", changed, **values)
        assert status == 200, status
        return out["filter-spec.data"]

    def call(self, output_id, changed, **values):
        """Run the callback that sets `output_id`. `changed` is the 'id.prop' that triggered it; `values`
        overrides inputs/state by 'id.prop' (pass as a dict via **{...}). Returns (status, outputs) where
        outputs maps 'id.prop' to the returned value; status 204 means PreventUpdate.
        A callback that reads the filter-spec store (roadmap 3.3a) gets the spec the real filter-spec callback makes
        from any panel values given, unless the test sets 'filter-spec.data' itself."""
        dep = self.find(output_id)
        if (output_id != "filter-spec" and "filter-spec.data" not in values
                and any(f"{x['id']}.{x['property']}" == "filter-spec.data" for x in dep["inputs"])):
            values = {**values, "filter-spec.data": self.spec_for(values)}

        def item(x):
            key = f"{x['id']}.{x['property']}"
            return {"id": x["id"], "property": x["property"],
                    "value": values.get(key, self.initial(x["id"], x["property"]))}

        outputs = [{"id": cid, "property": prop} for cid, prop in split_outputs(dep["output"])]
        body = {
            "output": dep["output"],
            "outputs": outputs if len(outputs) > 1 or dep["output"].startswith("..") else outputs[0],
            "inputs": [item(x) for x in dep["inputs"]],
            "state": [item(x) for x in dep["state"]],
            "changedPropIds": [changed] if changed else [],
        }
        # Plotly's encoder turns numpy values (e.g. the slider's start values) into plain JSON, as the browser sends
        resp = self.client.post("/_dash-update-component", data=json.dumps(body, cls=plotly.utils.PlotlyJSONEncoder),
                                content_type="application/json")
        if resp.status_code != 200:
            return resp.status_code, None
        payload = json.loads(resp.data)["response"]
        flat = {f"{cid}.{prop}": val for cid, props in payload.items() for prop, val in props.items()}
        return resp.status_code, flat
