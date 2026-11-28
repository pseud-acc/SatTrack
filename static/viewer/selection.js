// SatTrack viewer: selecting one object (roadmap 3.4; decisions D-018, D-019, D-023, D-024, D-054).
//
// Loaded by static/viewer/viewer.js once the globe has positions. A click or tap on a dot (or a search pick, or a
// shared link) selects it: the dot gets a ring and a name label that always shows, and a panel opens with
// - a headline anyone can read: name, type and status (operating vs transmitting, with dates), who owns, operates
//   and built it, live height and speed, the longitude it sits over for a GEO object, the launch, and the
//   constellation or system it belongs to ("one of 6,617 Starlink, 6,601 active");
// - "More details": identity, organisations, launch, orbit, physical and status sections, each with the source and
//   as-of date of its facts, and uncertain values marked where they show (an estimated mass, an approximate date,
//   an uncertain catalogue match);
// - toggles for the orbit (one period, the past half faded), the ground track (half a period back, one ahead) and a
//   camera that follows it (D-019); "Link" copies a link that opens the globe with it selected (D-024's hash,
//   version and satellite only), "Cite" copies a one-line citation.
// The panel is a card at the bottom on phones and a side panel on wider screens. Exact values only: masses in kg,
// no comparisons (owner, 28 Nov 2026). The details come from the object_detail dataset, which the worker fetches on
// the first selection (D-054); until then, or if it can't be had, the panel shows the objects dataset's fields.
// When zoomed in, the ~20 objects nearest the camera get name labels too (D-023).
// Every data string goes in with textContent.

const TYPE_LABEL = { "PAYLOAD": "Payload", "ROCKET BODY": "Rocket body", "DEBRIS": "Debris", "UNKNOWN": "Unknown type" };
const UNNAMED = "TBA - TO BE ASSIGNED";   // Space-Track's "not yet named"
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const STATUS_SOURCE = {
  gcat_psatcat: "GCAT payload catalogue",
  gcat_currentcat: "GCAT current catalogue",
  default_inactive: "no GCAT status record, so Inactive",
  space_track_object_type: "rocket bodies and debris are always Inactive (Space-Track type)",
};
// The orbit names of the filter panel's orbit hover cards (app/layouts/components/filters/orbit_filter.py ORBIT_HELP;
// a browser test holds the two to the same names)
export const ORBIT_NAMES = { LEO: "Low Earth orbit", MEO: "Medium Earth orbit", GEO: "Geostationary orbit",
                             GSO: "Geosynchronous orbit", HEO: "Highly elliptical orbit" };
const NEAR_LABELS = 20;                  // D-023
const NEAR_LABEL_HEIGHT_M = 6.0e6;       // camera height below which nearby objects get labels
const HASH_MAX = 64;
const SHARE_HOST = "https://www.sattrackapp.com/";

const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls;
  if (text !== undefined && text !== null) e.textContent = text; return e; };
const num = (v, digits = 0) => Number(v).toLocaleString("en-GB", { maximumFractionDigits: digits,
                                                                   minimumFractionDigits: digits });

export function displayName(r) {
  if (!r) return "";
  if (r.object_name === UNNAMED) return `Not yet named${r.object_id ? ` (${r.object_id})` : ""}`;
  return r.object_name || "(no name)";
}

// A GCAT vague date at the precision GCAT gives (batch 8 #24): never more digits than the source has. A trailing
// "?" (an uncertain date) reads "about ...". "current" has no date.
export function vagueDate(iso, precision) {
  if (!iso || !precision || precision.startsWith("current") || precision.startsWith("unknown")) return null;
  const unsure = precision.endsWith("?"), p = precision.replace("?", "");
  const y = Number(iso.slice(0, 4)), m = Number(iso.slice(5, 7)), d = Number(iso.slice(8, 10));
  let text;
  if (p === "millennium") text = `${Math.floor(y / 1000) * 1000}s`;
  else if (p === "century") text = `${Math.floor(y / 100) * 100}s`;
  else if (p === "decade") text = `${Math.floor(y / 10) * 10}s`;
  else if (p === "year") text = String(y);
  else if (p === "quarter") text = `Q${Math.floor((m - 1) / 3) + 1} ${y}`;
  else if (p === "month") text = `${MONTHS[m - 1]} ${y}`;
  else if (p === "day" || p === "centiday") text = `${d} ${MONTHS[m - 1]} ${y}`;
  else text = `${d} ${MONTHS[m - 1]} ${y}, ${iso.slice(11, 16)} UTC`;   // hour, minute, second
  return unsure ? `about ${text}` : text;
}

const dayText = (iso) => (iso ? vagueDate(iso, "day") : null);

// D-024's hash: format version and satellite only in 3.4 (3.5 adds time, mode, colour and types). Each field is
// checked against its allowlist; anything else is ignored.
export function parseHash(hash) {
  const text = String(hash || "").replace(/^#/, "");
  if (!text || text.length > HASH_MAX) return null;
  const params = new URLSearchParams(text);
  if (params.get("v") !== "1") return null;
  const sat = params.get("sat");
  if (!sat || !/^[1-9][0-9]{0,8}$/.test(sat)) return null;
  return { satcatId: Number(sat) };
}
export const hashFor = (satcatId) => `#v=1&sat=${satcatId}`;

// The status line: Space-Track's type and SatTrack's status, then GCAT's operating and transmitting detail.
export function statusLine(rec, det) {
  const parts = [TYPE_LABEL[rec.object_type] || "Unknown type", rec.operational_status || "Status unknown"];
  if (det) {
    const op = det.flag_still_operating, tx = det.flag_still_transmitting;
    const opEnd = vagueDate(det.end_operation_date, det.end_operation_date_precision);
    const txEnd = vagueDate(det.end_transmission_date, det.end_transmission_date_precision);
    if (op === 1) parts.push("still operating");
    else if (op === 0) parts.push(opEnd ? `stopped operating ${opEnd}` : "no longer operating");
    if (op !== 1 && tx === 1) parts.push("still transmitting");
    else if (op !== 1 && tx === 0 && txEnd && txEnd !== opEnd) parts.push(`stopped transmitting ${txEnd}`);
    // GCAT's "Z": "Zombie satellite: no longer controlled, but continues emitting a beacon signal"
    if (det.end_of_life_code === "Z") parts.push("no longer controlled, still sends a beacon");
  }
  return parts.join(" · ");
}

const list = (names, max = 3) => {
  const xs = (names || []).filter(Boolean);
  if (!xs.length) return null;
  return xs.length > max ? `${xs.slice(0, max).join(", ")} and ${xs.length - max} more` : xs.join(", ");
};

// The one-line citation "Cite" copies: what it is, the two sources with their as-of dates, and the link.
export function citation(rec, det, generatedAt) {
  const bits = [`${displayName(rec)} (SATCAT ${rec.satcat_id}${rec.object_id && rec.object_id !== "UNKNOWN" ? `, ${rec.object_id}` : ""})`];
  bits.push(`Orbital data: USSPACECOM via Space-Track.org, elements of ${dayText(rec.epoch) || "unknown date"}`);
  if (det && det.gcat_updated_at) bits.push(`details: GCAT (J. McDowell), ${dayText(det.gcat_updated_at)}`);
  const seen = generatedAt ? `, data of ${dayText(generatedAt)}` : "";
  return `${bits.join(". ")}. Via SatTrack${seen}: ${SHARE_HOST}${hashFor(rec.satcat_id)}`;
}

// Copy text: the Clipboard API where the page is a secure context, else a hidden textarea (the phone test server
// is plain http on the local network).
async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true; }
  } catch (e) { /* fall through */ }
  const area = Object.assign(document.createElement("textarea"), { value: text });
  area.setAttribute("readonly", ""); area.style.position = "fixed"; area.style.opacity = "0";
  document.body.append(area); area.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  area.remove();
  return ok;
}

export class Selection {
  constructor(viewer, S) {
    this.v = viewer;
    this.S = S;
    this.index = null;
    this.record = null;
    this.detail = null;
    this.live = null;
    this.toggles = { orbit: false, ground: false, follow: false };
    this.gen = 0;
    const C = viewer.Cesium, scene = viewer.widget.scene;
    this.C = C;
    this.ring = scene.primitives.add(new C.PointPrimitiveCollection()).add({
      position: C.Cartesian3.ZERO, show: false, pixelSize: 13, color: C.Color.TRANSPARENT,
      outlineColor: C.Color.fromCssColorString(this.token("--st-accent-hi", "#5fd3c4")), outlineWidth: 2,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    });
    this.labels = scene.primitives.add(new C.LabelCollection());
    this.nameLabel = this.labels.add({ show: false, text: "", font: "600 13px 'Source Sans 3', sans-serif",
      fillColor: C.Color.WHITE, outlineColor: C.Color.BLACK, outlineWidth: 3, style: C.LabelStyle.FILL_AND_OUTLINE,
      pixelOffset: new C.Cartesian2(10, -10), disableDepthTestDistance: Number.POSITIVE_INFINITY });
    this.near = [];
    this.nearIdx = [];
    this.lines = scene.primitives.add(new C.PolylineCollection());
    this.buildPanel();
    this.timer = setInterval(() => this.tick(), 1000);
    window.addEventListener("hashchange", () => this.fromHash());
  }

  token(name, fallback) {
    return (getComputedStyle(document.documentElement).getPropertyValue(name) || "").trim() || fallback;
  }

  // ---- selecting -------------------------------------------------------------------------------------------------
  async select(index, { fly = false, updateHash = true } = {}) {
    if (!Number.isInteger(index) || index < 0 || index >= this.v.ids.length) return;
    const gen = ++this.gen;
    this.index = index;
    this.detail = null;
    this.live = null;
    await this.v.call({ type: "pin", index });   // propagated even when the filters hide it
    const { record } = await this.v.call({ type: "info", index });
    if (gen !== this.gen) return;
    this.record = record;
    this.v.pinned = index;
    if (updateHash) this.setHash(hashFor(record.satcat_id));
    this.nameLabel.text = displayName(record);
    this.render();
    this.open(true);
    await this.v.resyncIfHidden(index);
    this.place();
    if (fly) this.flyTo();
    this.tick();
    this.publish();
    const group = record.satellite_constellation_name
      ? ["satellite_constellation_name", record.satellite_constellation_name]
      : record.primary_satellite_system_name ? ["primary_satellite_system_name", record.primary_satellite_system_name] : null;
    const [det, grp] = await Promise.all([
      this.v.call({ type: "detail", satcatId: record.satcat_id }),
      group ? this.v.call({ type: "group", field: group[0], value: group[1] }) : Promise.resolve(null),
    ]);
    if (gen !== this.gen) return;
    this.detail = det.record;
    this.detailAvailable = det.available;
    this.group = grp && group ? { name: group[1], kind: group[0], ...grp } : null;
    this.render();
    this.publish();
  }

  selectSatcat(satcatId, opts) {
    const i = Array.prototype.indexOf.call(this.v.ids, Number(satcatId));
    if (i < 0) return false;
    this.select(i, opts);
    return true;
  }

  clear({ updateHash = true } = {}) {
    this.gen++;
    this.index = null; this.record = null; this.detail = null; this.live = null; this.group = null;
    this.v.pinned = null;
    this.v.call({ type: "pin", index: null }).catch(() => {});
    if (this.toggles.follow) this.setFollow(false);
    this.toggles = { orbit: false, ground: false, follow: false };
    this.lines.removeAll();
    this.ring.show = false; this.nameLabel.show = false;
    if (updateHash) this.setHash("");
    this.open(false);
    this.publish();
    this.v.widget.scene.requestRender();
  }

  setHash(hash) {
    const url = `${location.pathname}${location.search}${hash}`;
    try { history.replaceState(history.state, "", url); } catch (e) { /* sandboxed pages */ }
  }

  fromHash() {
    const h = parseHash(location.hash);
    if (!h) return false;
    if (this.record && this.record.satcat_id === h.satcatId) return true;
    return this.selectSatcat(h.satcatId, { fly: true, updateHash: false });
  }

  flyTo() {
    const C = this.C, h = this.v.handles[this.index];
    if (!h) return;
    const p = h.position, r = C.Cartesian3.magnitude(p);
    if (!(r > 0)) return;
    const height = r - 6.371e6;
    const out = Math.max(2.5e6, height * 0.8);
    this.v.widget.scene.camera.flyTo({ destination: C.Cartesian3.multiplyByScalar(p, (r + out) / r, new C.Cartesian3()),
                                       duration: 1.5 });
  }

  // ---- every frame: the ring, the label and the follow camera sit on the selected dot -------------------------------
  frame() {
    // nearby labels follow their dots (Cesium copies positions, so they're set again each frame)
    for (let k = 0; k < this.near.length; k++) this.near[k].position = this.v.handles[this.nearIdx[k]].position;
    if (this.index === null) return;
    this.place();
    if (this.toggles.follow) {
      const C = this.C, cam = this.v.widget.scene.camera, h = this.v.handles[this.index];
      if (h && h.show) {
        const offset = C.Cartesian3.clone(cam.position);
        cam.lookAtTransform(C.Transforms.eastNorthUpToFixedFrame(h.position), offset);
      }
    }
  }

  place() {
    const h = this.index === null ? null : this.v.handles[this.index];
    const shown = !!(h && h.show);
    this.ring.show = shown; this.nameLabel.show = shown;
    if (shown) { this.ring.position = h.position; this.nameLabel.position = h.position; }
  }

  // ---- every second: live values, the orbit and ground track, nearby labels -----------------------------------------
  async tick() {
    this.nearbyLabels();
    if (this.index === null) return;
    const gen = this.gen, i = this.index, t = this.v.simTime();
    const live = await this.v.call({ type: "state", index: i, ms: t });
    if (gen !== this.gen) return;
    this.live = live;
    this.renderLive();
    if (this.toggles.orbit || this.toggles.ground) await this.drawLines(t);
    this.publish();
  }

  async drawLines(t) {
    const C = this.C, gen = this.gen, i = this.index;
    const want = [];
    if (this.toggles.orbit) want.push(this.v.call({ type: "track", index: i, ms: t, kind: "orbit" }).then((r) => ["orbit", r.positions]));
    if (this.toggles.ground) want.push(this.v.call({ type: "track", index: i, ms: t, kind: "ground" }).then((r) => ["ground", r.positions]));
    const got = await Promise.all(want);
    if (gen !== this.gen) return;
    this.lines.removeAll();
    const accent = C.Color.fromCssColorString(this.token("--st-accent-hi", "#5fd3c4"));
    for (const [kind, pos] of got) {
      const pts = [];
      if (kind === "orbit") for (let k = 0; k + 2 < pos.length; k += 3) pts.push(new C.Cartesian3(pos[k] * 1000, pos[k + 1] * 1000, pos[k + 2] * 1000));
      else for (let k = 0; k + 1 < pos.length; k += 2) pts.push(C.Cartesian3.fromDegrees(pos[k], pos[k + 1], 10000));
      if (pts.length < 2) continue;
      // the past faded: orbit points span one period centred on now, ground points half a period back, one ahead
      const split = kind === "orbit" ? Math.floor(pts.length / 2) : Math.floor(pts.length / 3);
      const width = kind === "orbit" ? 1.5 : 2;
      this.lines.add({ positions: pts.slice(0, split + 1), width, material: C.Material.fromType("Color", { color: accent.withAlpha(0.3) }) });
      this.lines.add({ positions: pts.slice(split), width, material: C.Material.fromType("Color", { color: accent.withAlpha(0.9) }) });
    }
    this.S.selectionLines = got.map(([kind, pos]) => ({ kind, points: pos.length / (kind === "orbit" ? 3 : 2) }));
    this.v.widget.scene.requestRender();
  }

  // D-023: when zoomed in, name labels on the ~20 shown objects nearest the camera.
  async nearbyLabels() {
    const C = this.C, scene = this.v.widget.scene, cam = scene.camera;
    const height = scene.globe.ellipsoid.cartesianToCartographic(cam.positionWC);
    const close = height && height.height < NEAR_LABEL_HEIGHT_M;
    if (!close) {
      if (this.near.length) { this.near.forEach((l) => this.labels.remove(l)); this.near = []; this.nearIdx = []; scene.requestRender(); }
      this.S.nearLabels = [];
      return;
    }
    const { handles, mask } = this.v, cp = cam.positionWC, best = [];
    for (let i = 0; i < handles.length; i++) {
      if (i === this.index || !(mask[i] || i === this.v.pinned) || !handles[i].show) continue;
      const d = C.Cartesian3.distanceSquared(cp, handles[i].position);
      if (best.length < NEAR_LABELS * 3 || d < best[best.length - 1][0]) {
        best.push([d, i]); best.sort((a, b) => a[0] - b[0]); if (best.length > NEAR_LABELS * 3) best.pop();
      }
    }
    const inView = best.filter(([, i]) => {
      const w = C.SceneTransforms.worldToWindowCoordinates(scene, handles[i].position);
      return w && w.x >= 0 && w.y >= 0 && w.x <= scene.canvas.clientWidth && w.y <= scene.canvas.clientHeight;
    }).slice(0, NEAR_LABELS).map(([, i]) => i);
    const { names } = await this.v.call({ type: "names", indices: inView });
    this.near.forEach((l) => this.labels.remove(l));
    this.nearIdx = inView;
    this.near = inView.map((i, k) => this.labels.add({ position: handles[i].position, text: names[k],
      font: "12px 'Source Sans 3', sans-serif", fillColor: C.Color.fromCssColorString(this.token("--st-muted", "#aab4c4")),
      outlineColor: C.Color.BLACK, outlineWidth: 2, style: C.LabelStyle.FILL_AND_OUTLINE,
      pixelOffset: new C.Cartesian2(7, -7) }));
    this.S.nearLabels = names;
    scene.requestRender();
  }

  setFollow(on) {
    const C = this.C, cam = this.v.widget.scene.camera;
    this.toggles.follow = on;
    if (!on) cam.lookAtTransform(C.Matrix4.IDENTITY);
    else {
      const h = this.v.handles[this.index];
      if (h && h.show) {
        const r = C.Cartesian3.magnitude(h.position), range = Math.max(1.5e6, (r - 6.371e6) * 1.2);
        cam.lookAt(h.position, new C.HeadingPitchRange(0, -Math.PI / 4, range));
      }
    }
    this.v.widget.scene.requestRender();
  }

  // ---- the panel -----------------------------------------------------------------------------------------------------
  buildPanel() {
    const p = this.panel = el("aside", "sattrack-select");
    p.id = "sattrack-select";
    p.hidden = true;
    p.setAttribute("aria-label", "Selected object");
    const head = el("div", "sattrack-select-head");
    this.nameEl = el("h2", "sattrack-select-name");
    // "–" puts the panel away as a pill and keeps the selection; "Clear" ends it (owner's option 2, 28 Nov 2026:
    // an unlabelled x read as "close the card" but dropped the satellite)
    const minimise = el("button", "sattrack-select-minimise", "–");
    minimise.type = "button"; minimise.id = "sattrack-select-minimise";
    minimise.setAttribute("aria-label", "Minimise"); minimise.title = "Minimise (keeps the satellite selected)";
    minimise.addEventListener("click", (e) => { e.stopPropagation(); this.minimise(true); });
    // "–" and "×" side by side, as on a window (owner, 28 Nov 2026): minimise keeps it, × clears it
    const close = el("button", "sattrack-select-close", "×");
    close.type = "button"; close.id = "sattrack-select-close";
    close.setAttribute("aria-label", "Clear the selection"); close.title = "Clear the selection";
    close.addEventListener("click", (e) => { e.stopPropagation(); this.clear(); });
    head.append(this.nameEl, minimise, close);
    // The pill: the selection's name while the panel is minimised; a tap brings the panel back
    const pill = this.pillEl = el("button", "sattrack-select-pill");
    pill.type = "button"; pill.id = "sattrack-select-pill"; pill.hidden = true;
    pill.addEventListener("click", () => this.minimise(false));
    this.pillNameEl = el("span", "sattrack-select-pill-name");
    pill.append(this.pillNameEl, el("span", "sattrack-select-pill-open", " ▴"));
    // On phones the card opens small ("peek": name, status, height and speed) so the globe stays visible;
    // "Details" expands it (owner, 28 Nov 2026: the full card covered over half the globe)
    this.peekEl = el("div", "sattrack-select-peek");
    this.peekLiveEl = el("span", "sattrack-select-peek-live");
    // "More ▴": a text link, plus a handle bar and the whole small card as tap targets (owner's option 3, 28 Nov 2026)
    const expand = this.expandEl = el("button", "sattrack-select-expand", "More ▴");
    expand.type = "button"; expand.id = "sattrack-select-expand"; expand.setAttribute("aria-expanded", "false");
    expand.addEventListener("click", (e) => { e.stopPropagation(); this.setExpanded(!this.panel.classList.contains("is-expanded")); });
    this.peekEl.append(this.peekLiveEl, expand);
    this.handleEl = el("div", "sattrack-select-handle");
    this.handleEl.setAttribute("aria-hidden", "true");
    // The handle steps down: expanded -> small card -> pill
    this.handleEl.addEventListener("click", (e) => {
      e.stopPropagation();
      if (this.dragged) { this.dragged = false; return; }
      if (this.panel.classList.contains("is-expanded")) this.setExpanded(false); else this.minimise(true);
    });
    // Dragging the card (owner, 28 Nov 2026: the bar promises a drag): down steps expanded -> small -> pill, up
    // expands; the card follows the finger downwards while dragging. Only on the phone card, never from a button or
    // from the scrolling details.
    const DRAG_PX = 40;
    let drag = null;
    const cardMode = () => p.classList.contains("is-card") &&
      (!window.matchMedia || window.matchMedia("(max-width: 576px)").matches);
    p.addEventListener("pointerdown", (e) => {
      if (!cardMode() || e.target.closest("button, details, a")) return;
      drag = { y: e.clientY, id: e.pointerId, moved: false };
      try { p.setPointerCapture(e.pointerId); } catch (err) { /* the finger can leave the card mid-drag */ }
    });
    p.addEventListener("pointermove", (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dy = e.clientY - drag.y;
      if (Math.abs(dy) > 8) drag.moved = true;
      p.style.transform = dy > 0 ? `translateY(${dy}px)` : "";
    });
    const endDrag = (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dy = e.clientY - drag.y;
      p.style.transform = "";
      this.dragged = drag.moved;
      drag = null;
      if (dy > DRAG_PX) {
        if (p.classList.contains("is-expanded")) this.setExpanded(false); else this.minimise(true);
      } else if (dy < -DRAG_PX && !p.classList.contains("is-expanded")) this.setExpanded(true);
    };
    p.addEventListener("pointerup", endDrag);
    p.addEventListener("pointercancel", (e) => { if (drag && e.pointerId === drag.id) { p.style.transform = ""; drag = null; } });
    p.addEventListener("click", (e) => {
      if (this.dragged) { this.dragged = false; return; }   // the end of a drag is not a tap
      if (!p.classList.contains("is-card") || p.classList.contains("is-expanded") || e.target.closest("button")) return;
      if (window.matchMedia && !window.matchMedia("(max-width: 576px)").matches) return;   // the card is phones only
      this.setExpanded(true);
    });
    this.statusEl = el("div", "sattrack-select-status");
    this.factsEl = el("dl", "sattrack-select-facts");
    const actions = el("div", "sattrack-select-actions");
    this.buttons = {};
    for (const [key, text] of [["orbit", "Orbit"], ["ground", "Ground track"], ["follow", "Follow"]]) {
      const b = el("button", "sattrack-select-toggle", text);
      b.type = "button"; b.id = `sattrack-select-${key}`; b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", () => this.toggle(key));
      this.buttons[key] = b; actions.append(b);
    }
    for (const [key, text] of [["link", "Link"], ["cite", "Cite"]]) {
      const b = el("button", "sattrack-select-copy", text);
      b.type = "button"; b.id = `sattrack-select-${key}`;
      b.addEventListener("click", () => this.copy(key, b));
      this.buttons[key] = b; actions.append(b);
    }
    this.more = el("details", "sattrack-select-more");
    this.more.id = "sattrack-select-more";
    this.more.append(el("summary", null, "More details"));
    this.sectionsEl = el("div", "sattrack-select-sections");
    this.more.append(this.sectionsEl);
    this.noteEl = el("div", "sattrack-select-note");
    // The drag bar, name, – and × stay in view while the details scroll (owner, 28 Nov 2026)
    const top = el("div", "sattrack-select-top");
    top.append(this.handleEl, head);
    p.append(top, this.statusEl, this.peekEl, this.factsEl, actions, this.more, this.noteEl);
    this.v.container.append(p, pill);
  }

  setExpanded(on) {
    this.panel.classList.toggle("is-expanded", on);
    this.expandEl.setAttribute("aria-expanded", String(on));
    this.expandEl.textContent = on ? "Less ▾" : "More ▴";
    this.S.selectionExpanded = on;
  }

  // Minimised: the panel hides and the pill shows; the ring, label, live values and lines carry on
  minimise(on) {
    if (this.index === null) return;
    this.minimised = on;
    this.panel.hidden = on;
    this.pillEl.hidden = !on;
    this.pillNameEl.textContent = this.record ? displayName(this.record) : "";
    this.S.selectionMinimised = on;
  }

  open(on) {
    if (on && (this.panel.hidden || this.minimised)) this.setExpanded(false);   // a new selection opens small on phones
    this.minimised = false;
    this.S.selectionMinimised = false;
    this.pillEl.hidden = true;
    this.panel.hidden = !on;
    this.panel.classList.add("is-card");   // a card at the bottom on phones (owner, 28 Nov 2026, after trying it)
    this.v.container.classList.toggle("has-selection", on);
  }

  toggle(key) {
    if (this.index === null) return;
    const on = !this.toggles[key];
    if (key === "follow") this.setFollow(on);
    else {
      this.toggles[key] = on;
      if (!this.toggles.orbit && !this.toggles.ground) { this.lines.removeAll(); this.S.selectionLines = []; this.v.widget.scene.requestRender(); }
      else this.drawLines(this.v.simTime());
    }
    this.buttons[key].setAttribute("aria-pressed", String(on));
    this.publish();
  }

  async copy(key, button) {
    if (!this.record) return;
    const text = key === "link" ? `${SHARE_HOST}${hashFor(this.record.satcat_id)}`
                                : citation(this.record, this.detail, this.S.generatedAt);
    const ok = await copyText(text);
    this.S.copied = { key, text, ok };
    const label = key === "link" ? "Link" : "Cite";
    button.textContent = ok ? "Copied" : "Copy failed";
    setTimeout(() => { button.textContent = label; }, 1500);
  }

  // note: shown after the value; kind "info" (where it came from) is muted, anything else is an uncertainty (warning)
  fact(dl, term, value, note, kind) {
    if (value === null || value === undefined || value === "") return;
    const dt = el("dt", null, term), dd = el("dd", null, value);
    if (note) dd.append(el("span", kind === "info" ? "sattrack-select-from" : "sattrack-select-unsure", ` ${note}`));
    dl.append(dt, dd);
    return dd;
  }

  render() {
    const r = this.record, d = this.detail;
    if (!r) return;
    this.nameEl.textContent = displayName(r);
    this.statusEl.textContent = statusLine(r, d);
    const f = this.factsEl;
    f.textContent = "";
    this.liveEls = {
      height: this.fact(f, "Height", "…"),
      speed: this.fact(f, "Speed", "…"),
    };
    if (r.orbit_class === "GEO") this.liveEls.lon = this.fact(f, "Over", "…");
    if (d) {
      this.fact(f, "Owner", list(d.owner_org_names) || r.owner_country);
      this.fact(f, "Operator", d.operator_name);
      this.fact(f, "Built by", list(d.manufacturer_org_names));
    } else this.fact(f, "Owner", r.owner_country);
    const launched = d ? vagueDate(d.launch_datetime, d.launch_datetime_precision) : (r.launch_year ? String(r.launch_year) : null);
    const how = d ? [d.launch_vehicle_type ? `on ${d.launch_vehicle_type}` : null, d.site_name ? `from ${d.site_name}` : null].filter(Boolean).join(" ") : "";
    this.fact(f, "Launched", launched ? `${launched}${how ? ` ${how}` : ""}` : null);
    if (this.group && this.group.total > 1) {
      this.fact(f, this.group.kind === "satellite_constellation_name" ? "Constellation" : "System",
        `One of ${num(this.group.total)} ${this.group.name} (${num(this.group.active)} active)`);
    } else if (r.satellite_constellation_name || r.primary_satellite_system_name) {
      this.fact(f, r.satellite_constellation_name ? "Constellation" : "System",
                r.satellite_constellation_name || r.primary_satellite_system_name);
    }
    this.renderLive();
    this.renderSections();
    this.noteEl.textContent = this.detailAvailable === false ? "More details aren't available right now." : "";
  }

  renderLive() {
    const L = this.live, E = this.liveEls || {};
    const set = (node, text) => { if (node) node.textContent = text; };
    if (!L || L.heightKm === null) {
      set(E.height, "not available"); set(E.speed, "not available"); set(E.lon, "not available");
      if (this.peekLiveEl) this.peekLiveEl.textContent = "";
      return;
    }
    // Orbit type with the height (owner, 28 Nov 2026: basic satellite info, on phones too): the class code on the
    // phone's small card, the full name in the panel
    const oc = this.record && this.record.orbit_class;
    if (this.peekLiveEl) {
      this.peekLiveEl.textContent = `${num(L.heightKm)} km${oc ? ` · ${oc}` : ""} · ${num(L.speedKms, 2)} km/s` +
        (oc === "GEO" ? ` · over ${num(Math.abs(L.lon), 1)}°${L.lon >= 0 ? "E" : "W"}` : "");
      this.peekLiveEl.title = oc && ORBIT_NAMES[oc] ? ORBIT_NAMES[oc] : "";
    }
    set(E.height, `${num(L.heightKm)} km` + (oc ? ` · ${ORBIT_NAMES[oc] ? `${ORBIT_NAMES[oc]} (${oc})` : oc}` : ""));
    set(E.speed, `${num(L.speedKms, 2)} km/s (${num(L.speedKms * 3600)} km/h)`);
    set(E.lon, `${num(Math.abs(L.lon), 1)}°${L.lon >= 0 ? "E" : "W"}`);
  }

  section(title, rows, source) {
    const rowsIn = rows.filter((x) => x && x[1] !== null && x[1] !== undefined && x[1] !== "");
    if (!rowsIn.length) return;
    const s = el("section", "sattrack-select-section");
    s.append(el("h3", null, title));
    const dl = el("dl");
    for (const [term, value, note, kind] of rowsIn) this.fact(dl, term, value, note, kind);
    s.append(dl);
    if (source) s.append(el("div", "sattrack-select-source", source));
    this.sectionsEl.append(s);
  }

  renderSections() {
    const r = this.record, d = this.detail, S = this.S;
    this.sectionsEl.textContent = "";
    const gcat = d && d.gcat_updated_at ? `Source: GCAT (J. McDowell, planet4589.org), catalogue of ${dayText(d.gcat_updated_at)}` : null;
    const epochAge = r.epoch ? (this.v.simTime() - Date.parse(`${r.epoch.slice(0, 19)}Z`)) / 86400000 : null;
    const elements = `Source: USSPACECOM via Space-Track.org, elements of ${dayText(r.epoch) || "unknown date"}` +
                     (epochAge !== null ? ` (${num(Math.max(0, epochAge), 1)} days old)` : "") +
                     ". Public element sets must not be used for conjunction assessment.";
    this.section("Identity", [
      ["SATCAT number", String(r.satcat_id)],
      ["International designator", r.object_id && r.object_id !== "UNKNOWN" ? r.object_id : null],
      ["GCAT ID", d && d.jcat, d && d.flag_catalog_match_uncertain === 1 ? "(GCAT's match to this number is uncertain)" : null],
      ["Type", TYPE_LABEL[r.object_type], d && d.object_type_source === "gcat" ? "(from GCAT: Space-Track says unknown)" : null, "info"],
      ["Programme", d && d.satellite_program],
      ["Mission", (r.mission_category_labels || []).join(", ") || null,
       d && d.mission_details_source === "inherited_parent" ? "(from the payload it came from)" : null, "info"],
    ], gcat);
    if (d) {
      this.section("Organisations", [
        ["Owners", list(d.owner_org_names, 10)],
        ["Owner country", (d.owner_country_codes || []).join(", ") || r.owner_country],
        ["Operator", d.operator_name],
        ["Manufacturers", list(d.manufacturer_org_names, 10)],
        ["Launch agency", list(d.launch_agency_org_names, 10)],
      ], gcat);
      const site = d.site_name ? `${d.site_name}${d.site_latitude !== null && d.site_longitude !== null
        ? ` (${num(Math.abs(d.site_latitude), 2)}°${d.site_latitude >= 0 ? "N" : "S"}, ${num(Math.abs(d.site_longitude), 2)}°${d.site_longitude >= 0 ? "E" : "W"})` : ""}` : null;
      this.section("Launch", [
        ["Date", vagueDate(d.launch_datetime, d.launch_datetime_precision)],
        ["Vehicle", [d.launch_vehicle_type, d.launch_vehicle_family && d.launch_vehicle_family !== d.launch_vehicle_type ? `(${d.launch_vehicle_family} family)` : null].filter(Boolean).join(" ") || null],
        ["Site", site],
        ["Flight", d.flight_id],
      ], gcat && (d.launch_details_source === "inherited_launch" ? `${gcat}; from its launch's record` : gcat));
    }
    this.section("Orbit", [
      ["Orbit class", r.orbit_class],
      ["Period", r.orbital_period ? `${num(r.orbital_period, 1)} min (${num(1440 / r.orbital_period, 1)} orbits a day)` : null],
      ["Inclination", r.inclination !== null && r.inclination !== undefined ? `${num(r.inclination, 2)}°` : null],
      ["Eccentricity", r.eccentricity !== null && r.eccentricity !== undefined ? num(r.eccentricity, 5) : null],
      ["Apogee / perigee", d && d.apoapsis !== null && d.periapsis !== null ? `${num(d.apoapsis)} / ${num(d.periapsis)} km` : null],
      ["Orbit conflict", d && d.flag_orbit_conflict === 1 ? "Space-Track still tracks it, but GCAT says it came down" : null],
    ], elements);
    if (d) {
      this.section("Physical", [
        ["Launch mass", d.mass_kg !== null ? `${num(d.mass_kg)} kg` : null, d.flag_mass_estimated === 1 ? "(estimate, good to about 20%)" : null],
        ["Dry mass", d.dry_mass_kg !== null ? `${num(d.dry_mass_kg)} kg` : null],
        ["Span", d.span_m !== null ? `${num(d.span_m, 1)} m` : null],
        ["Radar size", d.rcs_size ? `${d.rcs_size[0]}${d.rcs_size.slice(1).toLowerCase()} (Space-Track)` : null],
      ], gcat);
      this.section("Status", [
        ["Status", r.operational_status, STATUS_SOURCE[d.operational_status_source] ? `(${STATUS_SOURCE[d.operational_status_source]})` : null, "info"],
        ["Operating", d.flag_still_operating === 1 ? "Yes" : d.flag_still_operating === 0
          ? `No${vagueDate(d.end_operation_date, d.end_operation_date_precision) ? `, since ${vagueDate(d.end_operation_date, d.end_operation_date_precision)}` : ""}` : null],
        ["Transmitting", d.flag_still_transmitting === 1 ? "Yes" : d.flag_still_transmitting === 0
          ? `No${vagueDate(d.end_transmission_date, d.end_transmission_date_precision) ? `, since ${vagueDate(d.end_transmission_date, d.end_transmission_date_precision)}` : ""}` : null],
      ], gcat);
    }
    if (r.satellite_constellation_name || r.primary_satellite_system_name) {
      this.section("Group", [
        ["Constellation", r.satellite_constellation_name],
        ["System", r.primary_satellite_system_name],
      ], "Source: CelesTrak groups (Dr T.S. Kelso), completed from GCAT");
    }
    S.selectionSections = Array.from(this.sectionsEl.querySelectorAll("h3"), (h) => h.textContent);
  }

  // For the browser tests
  publish() {
    const r = this.record;
    this.S.selection = r ? { satcat_id: r.satcat_id, name: displayName(r), detail: !!this.detail,
                             live: this.live, toggles: { ...this.toggles } } : null;
  }

  destroy() {
    clearInterval(this.timer);
  }
}
