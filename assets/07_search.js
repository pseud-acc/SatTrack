/* Satellite search list (D-052; roadmap 3.9's browsable list, built early). Dash loads every assets/ script on
   every page; this one only acts when the tracker's #sat-search is in the page.

   - Fetches /data/search.json (app/core/search_index.py) once: after the globe's first positions, or 2.5 s after
     the panel appears, or at once when someone uses the box, so it never competes with the globe's start-up.
   - Shows a list you can scroll (space stations, then the newest launches, ...; the dataset's order) and narrows it
     as you type a name or a SATCAT number. Rows are added 60 at a time as you scroll, so the page never holds the
     whole catalogue's DOM.
   - Picking a row sets the hidden satcatid-filter-dropdown value (dash_clientside.set_props), which the panel's
     callbacks read like any other control; picking it again clears it. A clientside callback calls setSelected when
     the value changes elsewhere (a chip's x, Clear all).
   Every data string goes in through textContent. */
(function () {
  "use strict";
  var PAGE = 60, TYPES = { "PAYLOAD": "Payload", "ROCKET BODY": "Rocket body", "DEBRIS": "Debris" };
  var state = { el: null, records: null, loading: null, matches: [], shown: 0, selected: null, query: "" };

  function load() {
    if (state.records || state.loading || !state.el) return state.loading;
    var src = state.el.getAttribute("data-src") || "/data/search.json";
    status("Loading the satellite list…");
    state.loading = fetch(src, { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (doc) {
        state.records = doc.records.map(function (r) {
          r._name = (r.object_name || "").toLowerCase();
          r._id = String(r.satcat_id);
          return r;
        });
        render();
      })
      .catch(function () { state.loading = null; status("The satellite list couldn't load. Try again later."); });
    return state.loading;
  }

  function status(text) {
    var s = state.el && state.el.querySelector(".st-search-status");
    if (s) s.textContent = text || "";
  }

  function filter() {
    var q = state.query.trim().toLowerCase();
    if (!q) return state.records;
    var digits = /^\d+$/.test(q);
    return state.records.filter(function (r) {
      return digits ? r._id.indexOf(q) === 0 || r._name.indexOf(q) >= 0 : r._name.indexOf(q) >= 0;
    });
  }

  function meta(r) {
    var parts = ["SATCAT " + r.satcat_id];
    if (r.launch_year) parts.push(String(r.launch_year));
    parts.push(r.flag_space_station === 1 ? "Space station" : (TYPES[r.object_type] || "Unknown type"));
    if (r.operational_status) parts.push(r.operational_status);
    return parts.join(" · ");
  }

  function row(r) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "st-search-row" + (r._id === state.selected ? " is-picked" : "");
    b.setAttribute("role", "option");
    b.setAttribute("aria-selected", r._id === state.selected ? "true" : "false");
    b.dataset.id = r._id;
    var n = document.createElement("span"); n.className = "st-search-name"; n.textContent = r.object_name || "(no name)";
    var m = document.createElement("span"); m.className = "st-search-meta"; m.textContent = meta(r);
    b.appendChild(n); b.appendChild(m);
    return b;
  }

  function more() {
    var list = state.el.querySelector(".st-search-list"), end = Math.min(state.shown + PAGE, state.matches.length);
    var frag = document.createDocumentFragment();
    for (var i = state.shown; i < end; i++) frag.appendChild(row(state.matches[i]));
    list.appendChild(frag);
    state.shown = end;
  }

  function render() {
    if (!state.el || !state.records) return;
    var list = state.el.querySelector(".st-search-list");
    var matches = filter();
    // The picked satellite stays at the top of the unfiltered list, so it's easy to find and clear
    if (state.selected && !state.query.trim()) {
      var picked = state.records.filter(function (r) { return r._id === state.selected; });
      matches = picked.concat(matches.filter(function (r) { return r._id !== state.selected; }));
    }
    state.matches = matches; state.shown = 0;
    list.textContent = "";
    list.scrollTop = 0;
    more();
    status(state.query.trim() ? matches.length.toLocaleString() + " match" + (matches.length === 1 ? "" : "es")
                              : "Scroll to browse, or type to search");
  }

  function pick(id) {
    var value = state.selected === id ? null : id;
    state.selected = value;
    if (window.dash_clientside && window.dash_clientside.set_props) {
      window.dash_clientside.set_props("satcatid-filter-dropdown", { value: value });
    }
    render();
  }

  function mount(el) {
    state.el = el;
    el.textContent = "";
    var input = document.createElement("input");
    input.type = "search"; input.id = "sat-search-input"; input.className = "form-control st-search-input";
    input.placeholder = "Name or SATCAT number"; input.autocomplete = "off";
    input.setAttribute("aria-controls", "sat-search-list");
    var list = document.createElement("div");
    list.className = "st-search-list"; list.id = "sat-search-list"; list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", "Satellites");
    var s = document.createElement("div"); s.className = "st-search-status"; s.setAttribute("aria-live", "polite");
    el.appendChild(input); el.appendChild(list); el.appendChild(s);
    var timer = null;
    input.addEventListener("focus", load);
    input.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () { state.query = input.value; load(); render(); }, 120);
    });
    list.addEventListener("click", function (e) {
      var b = e.target.closest(".st-search-row");
      if (b) pick(b.dataset.id);
    });
    list.addEventListener("scroll", function () {
      if (list.scrollTop + list.clientHeight > list.scrollHeight - 80 && state.shown < state.matches.length) more();
    });
    if (state.records) render();
    else {
      status("");
      // After the globe's first positions (or 2.5 s), so the list never competes with the globe's start-up
      var started = Date.now();
      var wait = setInterval(function () {
        var v = window.sattrackViewer;
        if ((v && v.ready) || Date.now() - started > 2500 || !document.body.contains(el)) {
          clearInterval(wait);
          if (document.body.contains(el)) load();
        }
      }, 250);
    }
  }

  window.sattrackSearch = {
    setSelected: function (value) {
      var id = value === null || value === undefined || value === "" ? null : String(value);
      if (id === state.selected) return;
      state.selected = id;
      // Cleared from outside the list (a chip's x, Clear all): the search text goes too, so browsing starts over
      if (id === null && state.el) {
        var input = state.el.querySelector(".st-search-input");
        if (input) input.value = "";
        state.query = "";
      }
      render();
    },
    state: state,
  };

  // Mount whenever the tracker page (re)renders its search box
  new MutationObserver(function () {
    var el = document.getElementById("sat-search");
    if (el && el !== state.el) mount(el);
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
