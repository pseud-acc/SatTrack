"""Smoke tests: the Dash app as gunicorn serves it (run_app.server), on the sample data.

Scope: the app starts from the local sample (never S3); it serves its page shell and Dash's layout and
callback map; every callback id exists in the validation layout; no property is set by two callbacks; the URL
router returns the right page; every registered callback has a test file. Not in scope: browser rendering
and JavaScript, S3 reading (checked live after each deploy), the Heroku build (app-build.yml).
"""
import json
import re
from pathlib import Path

import plotly
import pytest

from _support import layout_by_id, split_outputs


def test_app_started_on_the_sample(app_module, sample_df):
    data = app_module.app_data["data"]
    assert data["data_source"] == "local"
    assert data["satcat_df"].equals(sample_df)


@pytest.mark.parametrize("path", ["/", "/_dash-layout", "/_dash-dependencies"])
def test_serves(client, path):
    # Dash returns the same page shell for every URL, so "/" stands for all pages; routing is tested below.
    assert client.get(path).status_code == 200


def test_no_property_set_by_two_callbacks(dependencies):
    outputs = [o for d in dependencies for o in split_outputs(d["output"])]
    duplicates = {o for o in outputs if outputs.count(o) > 1}
    assert not duplicates, f"set by more than one callback: {sorted(duplicates)}"


def test_every_callback_id_is_in_the_validation_layout(app_module, dependencies):
    """Dash's browser check: otherwise each page load logs 'ID not found in layout'."""
    ids = set(layout_by_id(app_module.app.validation_layout))
    used = {x["id"] for d in dependencies for x in d["inputs"] + d["state"]}
    used |= {cid for d in dependencies for cid, _ in split_outputs(d["output"])}
    assert not used - ids, f"missing from the layout: {sorted(used - ids)}"


@pytest.mark.parametrize("path, page", [
    ("/", "home"), ("/sat_visualisation", "viz"), ("/no-such-page", "home"), (None, "home"),
    ("/explore", "explore"), ("/explore/", "explore"), ("/explore/no-such-view", "explore"),
    ("/explore/systems", "systems"), ("/sources", "sources"), ("/faq", "faq")])
def test_router_returns_the_right_page(app_module, path, page):
    expected = {"home": lambda app: app_module.create_dash_layout_home(app),
                "viz": lambda app: app_module.create_dash_layout_sat_visualisations(app),
                "explore": lambda app: app_module.create_explore_layout(None),
                "systems": lambda app: app_module.create_explore_layout("systems"),
                "sources": lambda app: app_module.create_sources_layout(),
                "faq": lambda app: app_module.create_faq_layout()}[page](app_module.app)
    def as_json(component):
        return json.dumps(component, cls=plotly.utils.PlotlyJSONEncoder, sort_keys=True)
    assert as_json(app_module.display_page(path)) == as_json(expected)


def test_every_callback_has_a_test(dependencies):
    """Each callback's first output id must appear in a tests/app/test_callback_*.py file (the router's
    'page-content' is tested above). A new callback without a test fails here."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in Path(__file__).parent.glob("test_callback_*.py"))
    untested = []
    for d in dependencies:
        cid = split_outputs(d["output"])[0][0]
        if cid != "page-content" and not re.search(rf"['\"]{re.escape(cid)}['\".]", text):
            untested.append(cid)
    assert not untested, f"callbacks without a test: {untested}"
