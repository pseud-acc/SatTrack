"""E2E: the main user journeys in a real browser (headless Chromium), against the app on the sample data with
the clock frozen at the sample's download time.

Narrow scope (roadmap 0.5): each journey runs without browser errors (uncaught JS errors, console errors,
failed or 4xx/5xx requests to the app) and shows the right thing:
  1. Home opens and "Launch Tracker" leads to the tracker, with its nav link highlighted.
  2. The tracker opens on the globe (D-052) and shows as many objects as its panel counts.
  3. Picking one satellite in the search list shows its ground track on the 2D map.
  4. The list view shows the selected satellites, sorted by name.
  5. The search list can be browsed without typing, narrowed by typing, and picking from it filters the globe.
  6. Only the open tab holds a view: the 2D map exists only while its tab is open (D-052).
  7. On a phone, opening Filters makes no server request (D-052).
Not in scope: visual appearance, map tiles and other third-party resources, performance, the live site.
"""
import re

import pytest

from playwright.sync_api import expect

from _support import expected_ids, expected_object_ids, objects_sample

START_STATUS, START_ORBITS = "Active", ["LEO", "MEO", "GEO", "GSO", "HEO"]   # as it opens (3.3a: every orbit)
TIMEOUT = 60_000  # ms: figures render in software WebGL on CI runners
PLOT_2D = "2d-earth-satellite-plot"


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


def wait_for_globe(page):
    page.wait_for_function("() => window.sattrackViewer && window.sattrackViewer.ready", timeout=TIMEOUT)


def open_tracker(page, base_url):
    page.goto(base_url + "/sat_visualisation", wait_until="domcontentloaded")
    wait_for_globe(page)


def pick_satellite(page, satcat_id):
    """Pick one satellite in the search list (D-052) while the 2D map or list tab is open, where a pick filters to it
    (on the globe a pick selects it instead, roadmap 3.4): type its SATCAT number, click its row, wait for its chip."""
    page.locator("#sat-search-input").fill(str(satcat_id))
    row = page.locator(f'.st-search-row[data-id="{satcat_id}"]')
    expect(row).to_be_visible(timeout=TIMEOUT)
    row.click()
    expect(page.locator("#chip-satcatid")).to_be_visible(timeout=TIMEOUT)


def start_selection(sample_df, t_ref):
    year = [int(sample_df.LaunchYear.min()), int(sample_df.LaunchYear.max())]
    return expected_ids(sample_df, t_ref, status=START_STATUS, orbit=START_ORBITS, year=year)


def test_home_leads_to_the_tracker(page, base_url):
    page.goto(base_url + "/", wait_until="domcontentloaded")
    expect(page.get_by_text("Track Satellites in Real-Time")).to_be_visible(timeout=TIMEOUT)
    page.get_by_text("Launch Tracker", exact=True).click()
    expect(page).to_have_url(re.compile(r"/sat_visualisation$"))
    wait_for_globe(page)
    expect(page.locator("#nav-viz")).to_have_class(re.compile(r"\bactive\b"))
    assert page.errors == []


def test_tracker_opens_on_the_globe_showing_what_the_panel_counts(page, base_url):
    """D-052: the globe is the tracker's view. The loading bar is in the page from the start and hides once the
    satellites are placed; the globe shows as many objects as the panel counts (exact ids: tests/e2e/test_viewer.py)."""
    page.goto(base_url + "/sat_visualisation", wait_until="domcontentloaded")
    expect(page.locator("#globe .sattrack-loading")).to_be_attached(timeout=TIMEOUT)
    wait_for_globe(page)
    expect(page.locator("#globe .sattrack-loading")).to_have_class(re.compile(r"\bis-done\b"), timeout=TIMEOUT)
    for box, labels in (("#status-filter-checkbox", [START_STATUS]), ("#orbit-filter-checkbox", START_ORBITS)):
        for label in labels:
            expect(page.locator(box).get_by_label(label, exact=True)).to_be_checked()
    counted = int(page.locator("#filter-count .st-count-n").inner_text().replace(",", ""))
    shown = page.evaluate("window.sattrackViewer.shownCount + window.sattrackViewer.hiddenFailed")
    assert counted > 0 and shown == counted
    expect(page.locator("#sat-viz-tabs .nav-link.active")).to_have_text("Globe")
    assert page.get_by_role("tab", name="3D View").count() == 0   # the Plotly 3D view was removed (D-052)
    assert page.errors == []


def test_one_satellite_shows_its_ground_track(page, base_url, sample_df):
    open_tracker(page, base_url)
    sat = sample_df[(sample_df.Status == START_STATUS) & (sample_df.OrbitClass == "LEO")].iloc[0]
    page.get_by_role("tab", name="2D View").click()
    pick_satellite(page, sat.SatCatId)
    wait_for_traces(page, PLOT_2D, "lengths.includes(3600)")
    assert sorted(trace_lengths(page, PLOT_2D)) == [1, 3600]   # current position + one period of track
    assert page.errors == []


def test_list_view_shows_the_selected_satellites(page, base_url, sample_df, t_ref):
    open_tracker(page, base_url)
    page.get_by_role("tab", name="List View").click()
    rows = page.locator("#satellite-list tbody tr:has(td)")
    expect(rows.first).to_be_visible(timeout=TIMEOUT)
    # The list is built from the objects dataset (every object type; owner, 27 Nov 2026): at the start, the active
    # payloads sgp4 can place, sorted by name, with a Type column
    objects = objects_sample()
    expected = expected_object_ids(objects, t_ref)
    names = sorted(objects[objects.satcat_id.isin(expected)].object_name)
    page_size = 20   # viz_table.py
    expect(rows).to_have_count(min(page_size, len(expected)))
    shown = [rows.nth(i).locator("td").first.inner_text().strip() for i in range(rows.count())]
    assert shown == names[:page_size]
    headers = [h.strip() for h in page.locator("#satellite-list .column-header-name").all_inner_texts()]
    assert headers[:3] == ["Name", "Type", "SATCAT Number"]
    assert {rows.nth(i).locator("td").nth(1).inner_text().strip() for i in range(rows.count())} == {"Payload"}
    # Space junk mode: rocket bodies and debris join the list (they weren't in it before)
    page.get_by_label("Space junk mode").check()
    junk = expected_object_ids(objects, t_ref, status="All", types=["PAYLOAD", "ROCKET BODY", "DEBRIS"])
    all_names = sorted(objects[objects.satcat_id.isin(junk)].object_name)
    changed = next(i for i in range(page_size) if names[i] != all_names[i])   # the first row that must change
    expect(rows.nth(changed).locator("td").first).to_have_text(all_names[changed], timeout=TIMEOUT)
    shown = [rows.nth(i).locator("td").first.inner_text().strip() for i in range(rows.count())]
    assert shown == all_names[:page_size]
    assert len(junk) > len(expected)
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
        wait_for_globe(page)
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


def test_search_list_browses_narrows_and_picks(page, base_url):
    """D-052 (owner's option A; browse-first, owner 24 Nov 2026): the list shows satellites without typing, in the
    search dataset's order; typing narrows it. On the 2D map tab, picking one filters to it and names it on its chip;
    its chip's x clears the pick and the list starts over. (On the globe a pick selects instead: test_selection.py.)"""
    open_tracker(page, base_url)
    page.get_by_role("tab", name="2D View").click()
    rows = page.locator(".st-search-row")
    # Collapsed until used (owner, 27 Nov 2026); the toggle opens it for browsing
    expect(page.locator("#sat-search-list")).to_be_hidden()
    page.locator(".st-search-toggle").click()
    expect(rows.first).to_be_visible(timeout=TIMEOUT)
    doc = page.evaluate("fetch('/data/search.json').then(r => r.json())")
    # browsing lists what the filters show, in the list's order (roadmap 3.4, owner's option 3)
    matched = set(page.evaluate("[...window.sattrackViewer.matchedIds()]"))
    first = [str(r["satcat_id"]) for r in doc["records"] if r["satcat_id"] in matched][:5]
    assert [rows.nth(i).get_attribute("data-id") for i in range(5)] == first, "browsing starts in the list's order"
    target = next(r for r in doc["records"] if r["object_type"] == "PAYLOAD" and r["operational_status"] == "Active")
    page.locator("#sat-search-input").fill(target["object_name"][:6])
    expect(page.locator(".st-search-status")).to_contain_text("match", timeout=TIMEOUT)
    assert all(target["object_name"][:6].lower() in rows.nth(i).locator(".st-search-name").inner_text().lower()
               for i in range(min(5, rows.count())))
    changes = page.evaluate("window.sattrackViewer.filterChanges")
    pick_satellite(page, target["satcat_id"])
    expect(page.locator("#sat-search-list")).to_be_hidden()   # picking closes the list
    page.wait_for_function(f"() => window.sattrackViewer.filterChanges > {changes}", timeout=TIMEOUT)
    assert page.evaluate("window.sattrackViewer.shownIds()") == [target["satcat_id"]]
    expect(page.locator("#chip-satcatid-text")).to_contain_text(target["object_name"])
    page.locator("#chip-x-satcatid").click()
    page.wait_for_function("() => window.sattrackViewer.shownCount > 1", timeout=TIMEOUT)
    expect(page.locator("#sat-search-input")).to_have_value("")
    expect(page.locator(".st-search-row.is-picked")).to_have_count(0)
    assert page.errors == []


def test_only_the_open_tab_holds_a_view(page, base_url):
    """D-052 (owner, 27 Nov 2026: every tab was rendered at once): with the globe open there is no Plotly graph in
    the page and Plotly's script hasn't loaded; the 2D map exists only while its tab is open."""
    open_tracker(page, base_url)
    assert page.locator(".js-plotly-plot").count() == 0
    assert page.evaluate("() => !window.Plotly")
    page.get_by_role("tab", name="2D View").click()
    expect(page.locator(f"{by_id(PLOT_2D)} .js-plotly-plot")).to_be_attached(timeout=TIMEOUT)
    page.get_by_role("tab", name="Globe").click()
    expect(page.locator(".js-plotly-plot")).to_have_count(0, timeout=TIMEOUT)
    assert page.errors == []


def test_filters_open_on_a_phone_without_a_server_request(browser, base_url):
    """D-052 (owner, 27 Nov 2026: opening Filters on a phone waited for the server): the toggle runs in the browser."""
    context = browser.new_context(viewport={"width": 390, "height": 760}, is_mobile=True, has_touch=True)
    context.route(re.compile(r"^(?!http://127\.0\.0\.1[:/]).*"), lambda route: route.abort())   # offline, as `page`
    page = context.new_page()
    try:
        open_tracker(page, base_url)
        sent = []
        page.on("request", lambda r: sent.append(r.url) if "_dash-update-component" in r.url else None)
        expect(page.locator("#filter-collapse")).not_to_have_class(re.compile(r"\bshow\b"))
        page.locator("#toggle-filters").click()
        expect(page.locator("#filter-collapse")).to_have_class(re.compile(r"\bshow\b"), timeout=TIMEOUT)
        page.wait_for_timeout(500)
        assert sent == [], f"opening Filters called the server: {sent}"
    finally:
        context.close()


def test_orbit_info_icon_is_a_short_explainer(page, base_url):
    """Owner, 27 Nov 2026: the (i) card repeated the buttons' definitions. It explains orbit types in a line and
    points to the buttons' own cards."""
    open_tracker(page, base_url)
    page.locator("#orbit-info-icon").hover()
    card = page.get_by_role("tooltip")
    expect(card).to_be_visible(timeout=TIMEOUT)
    expect(card).to_contain_text("Hover over an orbit for its definition")
    expect(card).not_to_contain_text("Low Earth orbit")
    assert page.errors == []
