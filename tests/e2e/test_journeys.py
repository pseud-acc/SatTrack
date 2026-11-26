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

import pytest

from playwright.sync_api import expect

from _support import expected_ids

START_STATUS, START_ORBITS = "Active", ["LEO", "MEO", "GEO", "GSO", "HEO"]   # as it opens (3.3a: every orbit)
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
    """Pick one option in a dcc.Dropdown (Dash 4): open it, wait for its search box to have focus, search, click the
    option, and check the dropdown shows it. Typing straight after the click can lose keys on a slow CI runner."""
    page.locator(f"#{dropdown_id}").click()
    search = page.locator(".dash-dropdown-content .dash-dropdown-search")
    expect(search).to_be_focused(timeout=TIMEOUT)
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
    for box, labels in (("#status-filter-checkbox", [START_STATUS]), ("#orbit-filter-checkbox", START_ORBITS)):
        for label in labels:
            expect(page.locator(box).get_by_label(label, exact=True)).to_be_checked()
    expected = start_selection(sample_df, t_ref)
    assert len(expected) > 0
    assert trace_lengths(page, PLOT_3D)[1] == len(expected)   # trace 0 is the Earth, trace 1 the satellites
    expect(page.locator(f"{by_id(PLOT_3D)} canvas").first).to_be_visible()
    assert page.errors == []


def test_one_satellite_shows_its_ground_track(page, base_url, sample_df):
    open_tracker(page, base_url)
    sat = sample_df[(sample_df.Status == START_STATUS) & (sample_df.OrbitClass == "LEO")].iloc[0]
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


STYLE_PROBE = """() => ({
    sheets: [...document.styleSheets].map(s => s.href).filter(Boolean),
    font: getComputedStyle(document.body).fontFamily,
    bg: getComputedStyle(document.body).backgroundColor,
    bsVersion: getComputedStyle(document.documentElement).getPropertyValue('--bs-breakpoint-xxl').trim(),
    fontLoaded: document.fonts.check('16px "Source Sans 3"'),
})"""


@pytest.mark.parametrize("path, ready", [("/", "Track Satellites in Real-Time"), ("/sat_visualisation", None)])
def test_pages_use_only_the_self_hosted_design(page, base_url, path, ready):
    """3.12 (D-044): every stylesheet comes from the app itself (no CDN, no Google Fonts, no Font Awesome), Bootstrap 4
    and the Cyborg theme are gone (Bootstrap 5 defines --bs-breakpoint-xxl; 4 doesn't), and the page body uses the
    tokens: Source Sans 3 on the navy page colour (--st-bg #0a1220)."""
    page.goto(base_url + path, wait_until="domcontentloaded")
    if ready:
        expect(page.get_by_text(ready)).to_be_visible(timeout=TIMEOUT)
    else:
        wait_for_traces(page, PLOT_3D, "lengths.length >= 2")
    page.evaluate("document.fonts.ready")
    probe = page.evaluate(STYLE_PROBE)
    assert probe["sheets"] and all(h.startswith(base_url) for h in probe["sheets"]), probe["sheets"]
    assert not [h for h in probe["sheets"] if "cyborg" in h.lower() or "font-awesome" in h.lower()]
    assert probe["bsVersion"] == "1400px"
    assert probe["font"].startswith('"Source Sans 3"') and probe["fontLoaded"]
    assert probe["bg"] == "rgb(10, 18, 32)"
    assert not [u for u in page.offsite if "fonts.g" in u or "cdnjs" in u or "jsdelivr" in u or "bootstrapcdn" in u]
    assert page.errors == []


@pytest.mark.parametrize("orbit, name", [("LEO", "Low Earth orbit"), ("GEO", "Geostationary orbit"),
                                         ("HEO", "Highly elliptical orbit")])
def test_each_orbit_button_has_an_info_card_on_hover(page, base_url, orbit, name):
    """Owner, 26 Nov 2026: hovering an orbit button shows what that orbit class means."""
    open_tracker(page, base_url)
    page.locator("#orbit-filter-checkbox").get_by_text(orbit, exact=True).hover()
    card = page.get_by_role("tooltip")
    expect(card).to_be_visible(timeout=TIMEOUT)
    expect(card).to_contain_text(f"{orbit}: {name}")
    expect(card).to_contain_text("Height: ")                    # indicative height (owner, 26 Nov 2026)
    assert page.errors == []


def test_open_owner_list_stays_inside_the_panel(page, base_url, sample_df):
    """Owner, 26 Nov 2026: the open owner list sized itself to the longest name and hung past the filter panel. It is
    now as wide as its dropdown and long names wrap, so even the longest owner in the data fits."""
    longest = max(sample_df.Owner.dropna().unique(), key=len)
    open_tracker(page, base_url)
    page.locator("#more-owner summary").click()
    page.locator("#owner-filter-multi-dropdown").click()
    search = page.locator(".dash-dropdown-content .dash-dropdown-search")
    expect(search).to_be_focused(timeout=TIMEOUT)
    search.fill(longest)
    option = page.locator(".dash-dropdown-content").get_by_role("option", name=longest, exact=True)
    expect(option).to_be_visible(timeout=TIMEOUT)
    panel = page.locator(".st-panel").bounding_box()
    trigger = page.locator("#owner-filter-multi-dropdown").bounding_box()
    listbox = page.locator(".dash-dropdown-content").bounding_box()
    text = option.locator(".dash-options-list-option-text").bounding_box()
    assert listbox["x"] + listbox["width"] <= panel["x"] + panel["width"]
    assert abs(listbox["width"] - trigger["width"]) <= 1
    assert text["x"] + text["width"] <= listbox["x"] + listbox["width"]      # wrapped, not cut off or spilling
    # Owner, 26 Nov 2026: the tick box is centred on the first line's capitals. It sat ~4 px high in every dropdown,
    # then 0.75 px low when centred on the whole line; the capitals' middle is 0.05em above the line's middle (drawn
    # pixels of "A" at 100-200% zoom, Source Sans 3).
    tick = option.locator("input").bounding_box()
    line, size = option.locator(".dash-options-list-option-text").evaluate(
        "t => [parseFloat(getComputedStyle(t).lineHeight), parseFloat(getComputedStyle(t).fontSize)]")
    lift = (text["y"] + line / 2) - (tick["y"] + tick["height"] / 2)
    assert abs(lift - 0.05 * size) <= 0.5
    assert page.errors == []
