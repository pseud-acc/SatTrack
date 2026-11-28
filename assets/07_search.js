/* Satellite search list (D-052; roadmap 3.9's browsable list, built early). Dash loads every assets/ script on
   every page; this one only acts when the tracker's #sat-search is in the page.

   - Fetches /data/search.json (app/core/search_index.py) once: after the globe's first positions, or 2.5 s after
     the panel appears, or at once when someone uses the box, so it never competes with the globe's start-up.
   - Shows a list you can scroll (space stations, then the newest launches, ...; the dataset's order) and narrows it
     as you type a name or a SATCAT number. Rows are added 60 at a time as you scroll, so the page never holds the
     whole catalogue's DOM.
   - With the globe up, browsing lists only the objects the filters show (window.sattrackViewer.matchedIds), and
     typing searches everything: the globe's matches first, then the rest under "Hidden by your filters" (roadmap
     3.4, owner's option 3, 28 Nov 2026). The list follows each filter change ("sattrack-filtered" event).
   - Picking a row selects the object on the globe and flies to it, leaving the filters as they are (roadmap 3.4,
     owner, 28 Nov 2026). On the 2D map and list tabs, or without the globe, picking sets the hidden
     satcatid-filter-dropdown value (dash_clientside.set_props), which the panel's callbacks read like any other
     control; picking it again clears it. A clientside callback calls setSelected when the value changes elsewhere (a chip's x, Clear all).
   - The list is collapsed until the box is tapped or its toggle pressed (owner, 27 Nov 2026: an open list made the
     panel messy); picking a satellite, Esc, the toggle or a tap outside closes it again.
   - Objects Space-Track hasn't named yet ("TBA - TO BE ASSIGNED") show as "Not yet named" with their international
     designator, and can be found by it.
   Every data string goes in through textContent. */
(function () {
  "use strict";
  var PAGE = 60, TYPES = { "PAYLOAD": "Payload", "ROCKET BODY": "Rocket body", "DEBRIS": "Debris" };
  var UNNAMED = "TBA - TO BE ASSIGNED";
  var state = { el: null, records: null, loading: null, matches: [], shown: 0, selected: null, query: "", open: false };

  function displayName(r) {
    if (r.object_name === UNNAMED) return "Not yet named" + (r.object_id ? " (" + r.object_id + ")" : "");
    return r.object_name || "(no name)";
  }

  function load() {
    if (state.records || state.loading || !state.el) return state.loading;
    var src = state.el.getAttribute("data-src") || "/data/search.json";
    status("Loading the satellite list…");
    state.loading = fetch(src, { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (doc) {
        state.records = doc.records.map(function (r) {
          r._name = (displayName(r) + " " + (r.object_id || "")).toLowerCase();
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

  // Roadmap 3.4 (owner's option 3, 28 Nov 2026): browsing lists only what the filters put on the globe; typing finds
  // everything, the globe's matches first, then the rest under "Hidden by your filters". Without the globe (viewer
  // off or not ready) the list is the whole catalogue, as before.
  var DIVIDER = { _divider: true };
  function matched() {
    var v = window.sattrackViewer;
    return v && v.matchedIds ? v.matchedIds() : null;
  }

  function filter() {
    var q = state.query.trim().toLowerCase(), on = matched();
    state.onGlobe = on;
    var found = state.records;
    if (q) {
      var digits = /^\d+$/.test(q);
      found = state.records.filter(function (r) {
        return digits ? r._id.indexOf(q) === 0 || r._name.indexOf(q) >= 0 : r._name.indexOf(q) >= 0;
      });
    }
    if (!on) { state.hiddenCount = 0; return found; }
    var shown = [], hidden = [];
    for (var i = 0; i < found.length; i++) (on.has(found[i].satcat_id) ? shown : hidden).push(found[i]);
    state.shownCount = shown.length;
    state.hiddenCount = q ? hidden.length : 0;
    if (!q || !hidden.length) return shown;
    return shown.concat([DIVIDER], hidden);
  }

  function meta(r) {
    var parts = ["SATCAT " + r.satcat_id];
    if (r.launch_year) parts.push(String(r.launch_year));
    parts.push(r.flag_space_station === 1 ? "Space station" : (TYPES[r.object_type] || "Unknown type"));
    if (r.operational_status) parts.push(r.operational_status);
    return parts.join(" · ");
  }

  function row(r) {
    if (r._heading) {
      var h = document.createElement("div");
      h.className = "st-search-heading"; h.setAttribute("role", "presentation");
      h.textContent = r._heading + " · " + r.count.toLocaleString();
      return h;
    }
    if (r._divider) {
      var d = document.createElement("div");
      d.className = "st-search-divider"; d.setAttribute("role", "presentation");
      d.textContent = "Hidden by your filters (" + state.hiddenCount.toLocaleString() + ")";
      return d;
    }
    var b = document.createElement("button");
    b.type = "button";
    b.className = "st-search-row" + (r._id === state.selected ? " is-picked" : "");
    b.setAttribute("role", "option");
    b.setAttribute("aria-selected", r._id === state.selected ? "true" : "false");
    b.dataset.id = r._id;
    var n = document.createElement("span"); n.className = "st-search-name"; n.textContent = displayName(r);
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

  // Browsing in groups (roadmap 3.4, owner's option A, 28 Nov 2026): the list's order (space stations, payloads,
  // rocket bodies, debris; newest first in each) shown as headings with counts, and links above the list that jump
  // to each group, so the junk is one tap away instead of 16,000 rows down.
  var GROUPS = { "PAYLOAD": "Payloads", "ROCKET BODY": "Rocket bodies", "DEBRIS": "Debris" };
  function groupOf(r) { return r.flag_space_station === 1 ? "Space stations" : (GROUPS[r.object_type] || "Other objects"); }

  function grouped(items) {
    var out = [], jumps = [], last = null, head = null;
    for (var i = 0; i < items.length; i++) {
      var r = items[i];
      if (r._picked) { out.push(r); continue; }
      var g = groupOf(r);
      if (g !== last) {
        head = { _heading: g, count: 0 };
        jumps.push({ name: g, index: out.length, head: head });
        out.push(head);
        last = g;
      }
      head.count++;
      out.push(r);
    }
    state.jumps = jumps;
    return out;
  }

  function jumpBar() {
    var bar = state.el.querySelector(".st-search-jump");
    if (!bar) return;
    bar.textContent = "";
    var jumps = state.query.trim() ? [] : (state.jumps || []);
    bar.hidden = jumps.length < 2;
    jumps.forEach(function (j) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "st-search-jump-link";
      b.textContent = j.name + " " + j.head.count.toLocaleString();
      b.addEventListener("click", function (e) { e.stopPropagation(); startAt(j.index); });
      bar.appendChild(b);
    });
  }

  // Show the list from one position (a group's heading): rows before it aren't drawn, so a "back to the top" row
  // leads back.
  function startAt(index) {
    var list = state.el.querySelector(".st-search-list");
    list.textContent = "";
    list.scrollTop = 0;
    if (index > 0) {
      var top = document.createElement("button");
      top.type = "button"; top.className = "st-search-top"; top.textContent = "↑ Back to the top";
      top.addEventListener("click", function (e) { e.stopPropagation(); startAt(0); });
      list.appendChild(top);
    }
    state.shown = index;
    more();
  }

  function render() {
    if (!state.el || !state.records) return;
    var matches = filter();
    var browsing = !state.query.trim();
    // The picked satellite stays at the top of the unfiltered list, so it's easy to find and clear
    if (state.selected && browsing) {
      var picked = state.records.filter(function (r) { return r._id === state.selected; })
        .map(function (r) { return Object.assign({}, r, { _picked: true }); });
      matches = picked.concat(matches.filter(function (r) { return r._id !== state.selected; }));
    }
    var count = matches.length - (state.hiddenCount ? 1 : 0);
    state.jumps = [];
    if (browsing) matches = grouped(matches);
    state.matches = matches;
    jumpBar();
    startAt(0);
    var n = count;
    if (state.query.trim()) {
      status(n.toLocaleString() + " match" + (n === 1 ? "" : "es") +
             (state.onGlobe ? ", " + state.shownCount.toLocaleString() + " on the globe" : ""));
    } else {
      status(state.onGlobe ? n.toLocaleString() + " on the globe: scroll to browse, or type to search everything"
                           : "Scroll to browse, or type to search");
    }
  }

  function pick(id) {
    var value = state.selected === id ? null : id;
    state.selected = value;
    // Roadmap 3.4 (owner, 28 Nov 2026, after trying it on a phone): the pick selects the object on the globe and flies
    // there, without changing the filters, so what's around it stays shown (an object the filters hide is pinned);
    // picking it again clears the selection. Off the globe tab, the pick filters to it as before.
    // On the 2D map and list tabs, which have no selection, the pick still filters to the object (its ground track
    // on the 2D map).
    var v = window.sattrackViewer, globe = document.getElementById("globe");
    var onGlobe = !!(globe && globe.offsetParent !== null);
    if (v && v.ready && v.selectSatcat && onGlobe) {
      if (value !== null) v.selectSatcat(Number(value), { fly: true });
      else if (v.selection && String(v.selection.satcat_id) === String(id)) v.clearSelection();
    } else if (window.dash_clientside && window.dash_clientside.set_props) {
      window.dash_clientside.set_props("satcatid-filter-dropdown", { value: value });
    }
    render();
    setOpen(false);
  }

  function setOpen(open) {
    if (!state.el || state.open === open) return;
    state.open = open;
    state.el.classList.toggle("is-open", open);
    var t = state.el.querySelector(".st-search-toggle");
    if (t) { t.setAttribute("aria-expanded", open ? "true" : "false"); t.title = open ? "Hide the list" : "Browse the list"; }
    if (open) { load(); render(); }
  }

  function mount(el) {
    state.el = el;
    el.textContent = "";
    var input = document.createElement("input");
    input.type = "search"; input.id = "sat-search-input"; input.className = "form-control st-search-input";
    input.placeholder = "Name or SATCAT number"; input.autocomplete = "off";
    input.setAttribute("aria-controls", "sat-search-list");
    var toggle = document.createElement("button");
    toggle.type = "button"; toggle.id = "sat-search-toggle"; toggle.className = "st-search-toggle";
    toggle.setAttribute("aria-controls", "sat-search-list");
    toggle.setAttribute("aria-expanded", "false"); toggle.title = "Browse the list";
    toggle.setAttribute("aria-label", "Browse the satellite list");
    var box = document.createElement("div"); box.className = "st-search-box";
    var list = document.createElement("div");
    list.className = "st-search-list"; list.id = "sat-search-list"; list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", "Satellites");
    var s = document.createElement("div"); s.className = "st-search-status"; s.setAttribute("aria-live", "polite");
    box.appendChild(input); box.appendChild(toggle);
    var jump = document.createElement("div"); jump.className = "st-search-jump"; jump.hidden = true;
    jump.setAttribute("aria-label", "Jump to a group");
    el.appendChild(box); el.appendChild(jump); el.appendChild(list); el.appendChild(s);
    state.open = false;
    var timer = null;
    input.addEventListener("focus", function () { setOpen(true); });
    input.addEventListener("input", function () {
      setOpen(true);
      clearTimeout(timer);
      timer = setTimeout(function () { state.query = input.value; load(); render(); }, 120);
    });
    input.addEventListener("keydown", function (e) { if (e.key === "Escape") { setOpen(false); input.blur(); } });
    toggle.addEventListener("click", function () { setOpen(!state.open); });
    document.addEventListener("click", function (e) {
      if (state.open && state.el === el && !el.contains(e.target)) setOpen(false);
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

  // The globe's filters changed (or it got its first mask): the list follows
  window.addEventListener("sattrack-filtered", function () { if (state.records && state.el) render(); });

  // Mount whenever the tracker page (re)renders its search box
  new MutationObserver(function () {
    var el = document.getElementById("sat-search");
    if (el && el !== state.el) mount(el);
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
