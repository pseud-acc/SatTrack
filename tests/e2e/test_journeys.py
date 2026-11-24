"""E2E: the main user journeys in a real browser (headless Chromium), against the app on the sample data with
the clock frozen at the sample's download time.

Narrow scope (roadmap 0.5): each journey runs without browser errors (uncaught JS errors, console errors,
failed or 4xx/5xx requests to the app) and shows the right thing:
  1. Home opens and "Launch Tracker" leads to the tracker, with its nav link highlighted.
  2. The tracker opens on the 3D view and draws exactly the satellites its sidebar selects.
  3. Choosing one satellite by catalogue number shows its ground track on the 2D map.
  4. The list view shows the selected satellites, sorted by name.
Checks are by what the page shows (counts, rows, URLs) so they can be kept when Cesium replaces the Plotly
views (Phase 3). Not in scope: visual appearance, map tiles and other third-party resources, mobile layout,
performance, the live site.
"""
import re

from playwright.sync_api import expect

from _support import expected_ids

START_STATUS, START_ORBITS = ["Active"], ["LEO", "GEO"]   # the tracker's sidebar as it opens
TIMEOUT = 60_000  # ms: figures render in software WebGL on CI runners
PLOT_3D, PLOT_2D = "3d-earth-satellite-plot", "2d-earth-satellite-plot"


def by_id(element_id):
    """CSS for an id that starts with a digit (not allowed after '#')."""
    return f'[id="{element_id}"]'


def trace_lengths(page, element_id):
    """Number of points in each trace of the Plotly graph inside a dcc.Graph."""
    return page.evaluate(
        """id => (document.getElementById(id)?.querySelector('.js-plotly-plot')?.data || [])
                    .map(t => (t.x || t.lat || []).length)""", element_id)


def wait_for_traces(page, element_id, condition):
    page.wait_for_function(
        """([id, cond]) => {
               const d = document.getElementById(id)?.querySelector('.js-plotly-plot')?.data || [];
               return new Function('lengths', 'return ' + cond)(d.map(t => (t.x || t.lat || []).length));
           }""", arg=[element_id, condition], timeout=TIMEOUT)


def choose_in_dropdown(page, dropdown_id, label):
    """Pick one option in a dcc.Dropdown (Dash 4): open it, wait for its search box, search, click the option the
    server offers for that text (the search dropdowns start empty: server-side search), and check the dropdown shows
    it. fill() focuses the box itself; an empty dropdown leaves focus on its button, and typing straight after the
    click can lose keys on a slow CI runner."""
    page.locator(f"#{dropdown_id}").click()
    search = page.locator(".dash-dropdown-content .dash-dropdown-search")
    expect(search).to_be_visible(timeout=TIMEOUT)
    search.fill(label)
    page.locator(".dash-dropdown-content").get_by_role("option", name=label, exact=True).click()
    expect(page.locator(f"#{dropdown_id}")).to_contain_text(label, timeout=TIMEOUT)


def open_tracker(page, base_url):
    page.goto(base_url + "/sat_visualisation", wait_until="domcontentloaded")
    wait_for_traces(page, PLOT_3D, "lengths.length >= 2")


def start_selection(sample_df, t_ref):
    year = [int(sample_df.LaunchYear.min()), int(sample_df.LaunchYear.max())]
    return expected_ids(sample_df, t_ref, status=START_STATUS, orbit=START_ORBITS, year=year)


def test_home_leads_to_the_tracker(page, base_url):
    page.goto(base_url + "/", wait_until="domcontentloaded")
    expect(page.get_by_text("Track Satellites in Real-Time")).to_be_visible(timeout=TIMEOUT)
    page.get_by_text("Launch Tracker", exact=True).click()
    expect(page).to_have_url(re.compile(r"/sat_visualisation$"))
    wait_for_traces(page, PLOT_3D, "lengths.length >= 2")
    expect(page.locator("#nav-viz")).to_have_class(re.compile(r"\bactive\b"))
    assert page.errors == []


def test_tracker_draws_the_selected_satellites(page, base_url, sample_df, t_ref):
    open_tracker(page, base_url)
    for box, labels in (("#status-filter-checkbox", START_STATUS), ("#orbit-filter-checkbox", START_ORBITS)):
        for label in labels:
            expect(page.locator(box).get_by_label(label, exact=True)).to_be_checked()
    expected = start_selection(sample_df, t_ref)
    assert len(expected) > 0
    assert trace_lengths(page, PLOT_3D)[1] == len(expected)   # trace 0 is the Earth, trace 1 the satellites
    expect(page.locator(f"{by_id(PLOT_3D)} canvas").first).to_be_visible()
    assert page.errors == []


def test_one_satellite_shows_its_ground_track(page, base_url, sample_df):
    open_tracker(page, base_url)
    sat = sample_df[sample_df.Status.isin(START_STATUS) & (sample_df.OrbitClass == "LEO")].iloc[0]
    choose_in_dropdown(page, "satcatid-filter-dropdown", str(sat.SatCatId))
    page.get_by_role("tab", name="2D View").click()
    wait_for_traces(page, PLOT_2D, "lengths.includes(3600)")
    assert sorted(trace_lengths(page, PLOT_2D)) == [1, 3600]   # current position + one period of track
    assert page.errors == []


def test_list_view_shows_the_selected_satellites(page, base_url, sample_df, t_ref):
    open_tracker(page, base_url)
    page.get_by_role("tab", name="List View").click()
    rows = page.locator("#satellite-list tbody tr:has(td)")
    expect(rows.first).to_be_visible(timeout=TIMEOUT)
    expected = start_selection(sample_df, t_ref)
    names = sorted(sample_df[sample_df.SatCatId.isin(expected)].ObjectName)
    page_size = 20   # viz_table.py
    expect(rows).to_have_count(min(page_size, len(expected)))
    shown = [rows.nth(i).locator("td").first.inner_text().strip() for i in range(rows.count())]
    assert shown == names[:page_size]
    assert page.errors == []
