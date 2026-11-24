// SatTrack Cesium viewer (roadmap 3.2; docs/cesium-architecture.md; decisions D-013 to D-029).
//
// Loaded only on the tracker page, and only when the viewer flag is on: the Dash clientside bridge
// (app/callbacks/callback_viewer.py) injects this module and calls mount() with the viewer-config store. It mounts
// Cesium into the empty div#globe, which no Dash callback ever writes to (D-013).
//
// - Positions come from static/viewer/worker.js, which propagates every shown object on a grid of simulation time;
//   this thread only interpolates linearly between the two samples around the current time (D-015). The grid step
//   adapts between 0.25 and 10 s of simulation time to the worker's speed, the frame rate and the play speed.
// - One PointPrimitiveCollection for every object, coloured by type with a legend; payloads by default, toggles for
//   rocket bodies and debris and a "space junk mode" switch for both; UNKNOWN never shown (D-016, D-017).
// - Natural Earth II from the self-hosted Cesium, no Cesium ion (D-014, D-022). SatTrack's credits replace
//   Cesium's credit display. Every data string is written with textContent.
// - The clock is corrected by the offset between this device and the server's Date header.
// - window.sattrackViewer exposes state and timings for the browser tests (parity and the D-027 budget).

const TYPES = ["PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"];
const STYLE = {   // Okabe-Ito colours (colour-blind safe), with a dark outline so points read on natural colour (D-022)
  "PAYLOAD": { label: "Payloads", colour: "#56B4E9" },
  "ROCKET BODY": { label: "Rocket bodies", colour: "#E69F00" },
  "DEBRIS": { label: "Debris", colour: "#CC79A7" },
};
const STEPS = [0.25, 0.5, 1, 2, 5, 10];     // seconds of simulation time between worker samples (D-015)
const KEEP = 600;                            // timings kept per series
const CREDITS = [
  ["Orbital data: ", "USSPACECOM via Space-Track.org", "https://www.space-track.org/",
   ". Public element sets must not be used for conjunction (collision) assessment."],
  ["Launch and owner details: ", "GCAT (J. McDowell, planet4589.org)", "https://planet4589.org/space/gcat/", ", CC-BY."],
  ["Globe: ", "CesiumJS", "https://cesium.com/platform/cesiumjs/", " (Apache-2.0). "],
  ["Positions: ", "satellite.js", "https://github.com/shashwatak/satellite-js", " (MIT). "],
  ["Imagery: ", "Natural Earth", "https://www.naturalearthdata.com/", " (public domain)."],
];

const S = window.sattrackViewer = window.sattrackViewer || {};
Object.assign(S, {
  version: 1, ready: false, error: null, engine: null, step: 1, clockOffsetMs: 0, count: 0, failed: [],
  shownCount: 0, hiddenFailed: 0, typeCounts: {}, types: { "PAYLOAD": true, "ROCKET BODY": false, "DEBRIS": false },
  marks: {}, frameMs: [], applyMs: [], workerMs: [], hint: null,
});
const push = (arr, v) => { arr.push(v); if (arr.length > KEEP) arr.shift(); };
const avg = (a) => (a.length ? a.reduce((s, v) => s + v, 0) / a.length : 0);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text; return e; };

let current = null;   // the mounted instance

function loadOnce(id, make) {
  const found = document.getElementById(id);
  if (found) return found._loaded;
  const node = make();
  node.id = id;
  node._loaded = new Promise((resolve, reject) => {
    node.addEventListener("load", resolve);
    node.addEventListener("error", () => reject(new Error(`could not load ${node.src || node.href}`)));
  });
  document.head.appendChild(node);
  return node._loaded;
}

// Cesium's ES module build (index.js: 4.8 MB against Cesium.js's 6.1 MB, and no global). It compiles small WebAssembly
// modules (meshoptimizer) at load, which the policy allows ('wasm-unsafe-eval'); its one (0,eval)("this") (bundled
// Knockout) is patched to globalThis at vendoring, so the policy never needs 'unsafe-eval' (D-041).
async function loadCesium(config) {
  window.CESIUM_BASE_URL = config.cesium;   // where Cesium finds its workers and assets
  const [Cesium] = await Promise.all([
    import(`${config.cesium}index.js`),
    loadOnce("sattrack-cesium-css", () => Object.assign(document.createElement("link"),
      { rel: "stylesheet", href: `${config.cesium}Widgets/CesiumWidget/CesiumWidget.css` })),
    loadOnce("sattrack-viewer-css", () => Object.assign(document.createElement("link"),
      { rel: "stylesheet", href: config.css })),
  ]);
  if (!Cesium || !Cesium.CesiumWidget) throw new Error("Cesium did not load");
  return Cesium;
}

// Offset (ms) to add to this device's clock: the server's Date header (whole seconds, so +500 ms centres it) against
// the middle of the request. Only applied beyond 2 s, so a correct device clock isn't jittered by the rounding.
export function clockOffset(header, sentMs, receivedMs) {
  const server = Date.parse(header || "");
  if (!Number.isFinite(server)) return 0;
  const offset = server + 500 - (sentMs + receivedMs) / 2;
  return Math.abs(offset) > 2000 ? Math.round(offset) : 0;
}

// The server's clock, from the Date header of a HEAD request for the data file (no body), timed on this thread.
async function serverClock(url) {
  try {
    const sentMs = Date.now();
    const r = await fetch(url, { method: "HEAD", cache: "no-store" });
    return clockOffset(r.headers.get("Date"), sentMs, Date.now());
  } catch (e) { return 0; }
}

class Viewer {
  constructor(container, config) {
    this.container = container;
    this.config = config;
    this.worker = null;
    this.widget = null;
    this.nextId = 0;
    this.pending = new Map();
    this.destroyed = false;
    this.gen = 0;
  }

  call(msg) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ ...msg, id });
    });
  }

  onWorker({ data }) {
    if (data.type === "meta") { this.metaResolve(data); return; }
    if (data.type === "ready") { S.marks.ready = performance.now(); this.readyResolve(data); return; }
    if (data.type === "records") { S.failed = data.failed; S.recordsBuilt = true; return; }
    if (data.type === "error" && data.id === undefined) {
      const err = new Error(data.error);
      this.metaReject(err); this.readyReject(err);
      return;
    }
    const p = this.pending.get(data.id);
    if (!p) return;
    this.pending.delete(data.id);
    if (data.type === "error") p.reject(new Error(data.error)); else p.resolve(data);
  }

  async start() {
    S.marks.start = performance.now();
    // The worker fetches and parses the data while this thread loads Cesium.
    this.worker = new Worker(this.config.worker, { type: "module" });
    const meta = new Promise((res, rej) => { this.metaResolve = res; this.metaReject = rej; });
    const ready = new Promise((res, rej) => { this.readyResolve = res; this.readyReject = rej; });
    meta.catch(() => {}); ready.catch(() => {});   // handled where awaited
    this.worker.onmessage = (e) => this.onWorker(e);
    this.worker.onerror = (e) => {
      const err = new Error(`worker: ${e.message || "failed to load"}`);
      this.metaReject(err); this.readyReject(err);
    };
    // The first two samples (on this device's clock; a large server offset resamples on the first frame) come back
    // with the worker's "ready", so the first positions need no extra round trip.
    this.step = S.step = 1;
    const t0 = Math.floor(Date.now() / 1000) * 1000;
    this.worker.postMessage({ type: "init", data: this.config.data, satellite: this.config.satellite,
                              first: { dates: [t0, t0 + 1000], types: this.activeCodes() } });
    const clock = serverClock(this.config.data);

    const Cesium = await loadCesium(this.config);
    S.marks.cesium = performance.now();
    if (this.destroyed) return;
    this.Cesium = Cesium;
    // SatTrack's credits replace Cesium's: its credit display goes into a detached element that is never shown.
    this.widget = new Cesium.CesiumWidget(this.container, {
      baseLayer: Cesium.ImageryLayer.fromProviderAsync(
        Cesium.TileMapServiceImageryProvider.fromUrl(Cesium.buildModuleUrl("Assets/Textures/NaturalEarthII"))),
      skyBox: false, creditContainer: document.createElement("div"), shouldAnimate: true,
      showRenderLoopErrors: false, msaaSamples: 1,
    });
    if (window.matchMedia && window.matchMedia("(pointer: coarse)").matches) this.widget.targetFrameRate = 30;  // D-027
    S.webgl = (() => { try { const gl = this.widget.scene.context._gl, ext = gl.getExtension("WEBGL_debug_renderer_info");
      return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); } catch (e) { return null; } })();
    S.marks.viewer = performance.now();

    const m = await meta;
    S.marks.data = performance.now();
    if (this.destroyed) return;
    S.count = m.count;
    S.generatedAt = m.generatedAt;
    S.clockOffsetMs = await clock;
    this.ids = m.ids;
    this.typeCodes = m.types;
    S.typeCounts = Object.fromEntries(TYPES.map((t) => [t, 0]));
    for (const c of this.typeCodes) S.typeCounts[TYPES[c]]++;
    this.widget.clock.currentTime = Cesium.JulianDate.fromDate(new Date(Date.now() + S.clockOffsetMs));

    this.points = this.widget.scene.primitives.add(new Cesium.PointPrimitiveCollection());
    const colours = TYPES.map((t) => Cesium.Color.fromCssColorString(STYLE[t] ? STYLE[t].colour : "#ffffff"));
    const outline = Cesium.Color.fromCssColorString("#101010");
    this.handles = Array.from(this.typeCodes, (code) => this.points.add({
      position: Cesium.Cartesian3.ZERO, show: false, pixelSize: 4, color: colours[code],
      outlineColor: outline, outlineWidth: 1,
    }));
    this.buildPanel();

    // First positions: the two samples computed with "ready", then one sample ahead always in flight.
    const init = await ready;
    if (this.destroyed) return;
    S.engine = `worker-${init.engine}`;
    S.builtBeforeReady = init.built;   // records built before the first positions (D-042)
    S.failed = init.failed;
    push(S.workerMs, init.first.ms / 2);
    [this.a, this.b] = init.first.dates.map((t, i) => ({ t, pos: init.first.positions[i] }));
    this.c = null;
    this.requestNext();
    this.apply(this.simTime());
    S.marks.firstPositions = performance.now();
    S.firstPositionsMs = S.marks.firstPositions - S.marks.start;
    this.lastFrame = performance.now();
    this.widget.scene.preRender.addEventListener(() => this.frame());
    this.controller = setInterval(() => this.adapt(), 2000);
    this.statusTimer = setInterval(() => this.updateStatus(), 1000);
    S.ready = true;
    this.updateStatus();
  }

  simTime() { return this.Cesium.JulianDate.toDate(this.widget.clock.currentTime).getTime(); }

  activeCodes() { return TYPES.map((t, i) => (S.types[t] ? i : -1)).filter((i) => i >= 0); }

  async sample(ms) {
    const r = await this.call({ type: "compute", dates: [ms], types: this.activeCodes() });
    push(S.workerMs, r.ms);
    return { t: ms, pos: r.positions[0], types: this.activeCodes().join() };
  }

  requestNext() {
    const nt = this.b.t + this.step * 1000, gen = this.gen;
    this.sample(nt).then((r) => { if (gen === this.gen) this.c = r; }).catch((e) => this.fail(e));
  }

  frame() {
    const now = performance.now();
    push(S.frameMs, now - this.lastFrame);
    this.lastFrame = now;
    const t = this.simTime();
    while (t >= this.b.t && this.c) { this.a = this.b; this.b = this.c; this.c = null; this.requestNext(); }
    // A time jump outside the samples (e.g. the tab was hidden): resample around the new time.
    if (!this.resyncing && (t < this.a.t || t > this.b.t + 2 * this.step * 1000)) this.resync(t);
    const t1 = performance.now();
    this.apply(t);
    push(S.applyMs, performance.now() - t1);
  }

  async resync(t) {
    this.resyncing = true;
    const gen = ++this.gen;   // samples requested before this belong to the old window
    try {
      const t0 = Math.floor(t / 1000) * 1000;
      const [a, b] = await Promise.all([this.sample(t0), this.sample(t0 + this.step * 1000)]);
      if (gen !== this.gen) return;
      this.a = a; this.b = b; this.c = null; this.requestNext();
    } catch (e) { this.fail(e); } finally { this.resyncing = false; }
  }

  // Interpolate between samples a and b and move the points (metres). Objects of hidden types, and failed objects
  // (NaN in either sample), are hidden.
  apply(t) {
    const { a, b, handles, typeCodes } = this;
    const f = b.t > a.t ? Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t))) : 0;
    const scratch = this.scratch || (this.scratch = new this.Cesium.Cartesian3());
    const shownTypes = TYPES.map((name) => !!S.types[name]);
    let shown = 0, bad = 0;
    for (let i = 0; i < handles.length; i++) {
      const h = handles[i];
      if (!shownTypes[typeCodes[i]]) { if (h.show) h.show = false; continue; }
      const j = 3 * i;
      const x = a.pos[j] + (b.pos[j] - a.pos[j]) * f, y = a.pos[j + 1] + (b.pos[j + 1] - a.pos[j + 1]) * f,
            z = a.pos[j + 2] + (b.pos[j + 2] - a.pos[j + 2]) * f;
      if (!(Number.isFinite(x) && Number.isFinite(y) && Number.isFinite(z))) { if (h.show) h.show = false; bad++; continue; }
      scratch.x = x * 1000; scratch.y = y * 1000; scratch.z = z * 1000;
      h.position = scratch;   // the setter copies
      if (!h.show) h.show = true;
      shown++;
    }
    S.shownCount = shown;
    S.hiddenFailed = bad;
  }

  // Step controller (D-015): one worker pass may use at most a quarter of the wall time between samples, never more
  // often than once a wall second at 1x; slow frames (below 20 fps) double the interval. Snapped up to STEPS.
  adapt() {
    const w = avg(S.workerMs.slice(-5)), frame = avg(S.frameMs.slice(-60));
    const speed = Math.abs(this.widget.clock.multiplier) || 1;
    let wallS = Math.max(1, (4 * w) / 1000);
    if (frame > 50) wallS *= 2;
    const want = speed * wallS;
    const step = STEPS.find((s) => s >= want) || STEPS[STEPS.length - 1];
    if (step !== this.step) { this.step = S.step = step; }
    // D-027: suggest switching debris off when junk mode runs below 20 fps for 5 s; never do it automatically.
    const slow = S.types.DEBRIS && S.frameMs.length > 60 && avg(S.frameMs.slice(-150)) > 50;
    S.hint = slow ? "Running slowly: switching debris off makes the globe smoother." : null;
    if (this.hintEl) this.hintEl.textContent = S.hint || "";
  }

  setTypes(types) {
    Object.assign(S.types, types);
    S.types.UNKNOWN = false;   // never shown (D-011, D-016)
    this.syncPanel();
    // Newly shown types have no positions in the current samples: resample now rather than wait a step.
    if (this.a) this.resync(this.simTime());
  }

  buildPanel() {
    const panel = el("div", "sattrack-viewer-panel");
    panel.setAttribute("aria-label", "Globe legend and object types");
    const legend = el("ul", "sattrack-viewer-legend");
    this.boxes = {};
    for (const [type, style] of Object.entries(STYLE)) {
      const li = el("li"), label = el("label"), box = el("input"), swatch = el("span", "sattrack-viewer-swatch");
      box.type = "checkbox";
      box.dataset.type = type;
      box.addEventListener("change", () => this.setTypes({ [type]: box.checked }));
      swatch.style.backgroundColor = style.colour;
      label.append(box, swatch, el("span", null, `${style.label} (${(S.typeCounts[type] || 0).toLocaleString()})`));
      li.append(label);
      legend.append(li);
      this.boxes[type] = box;
    }
    const junkLabel = el("label", "sattrack-viewer-junk"), junk = el("input");
    junk.type = "checkbox";
    junk.setAttribute("role", "switch");
    junk.addEventListener("change", () => this.setTypes({ "ROCKET BODY": junk.checked, "DEBRIS": junk.checked }));
    junkLabel.append(junk, el("span", null, "Space junk mode"));
    this.junk = junk;
    this.statusEl = el("div", "sattrack-viewer-status", "Loading…");
    this.hintEl = el("div", "sattrack-viewer-hint");
    const credits = el("div", "sattrack-viewer-credits");
    for (const [before, name, href, after] of CREDITS) {
      const line = el("div"), link = el("a", null, name);
      link.href = href; link.target = "_blank"; link.rel = "noopener noreferrer";
      line.append(document.createTextNode(before), link, document.createTextNode(after));
      credits.append(line);
    }
    panel.append(legend, junkLabel, this.statusEl, this.hintEl);
    this.container.append(panel, credits);
    this.syncPanel();
  }

  syncPanel() {
    if (!this.boxes) return;
    for (const [type, box] of Object.entries(this.boxes)) box.checked = !!S.types[type];
    this.junk.checked = !!(S.types["ROCKET BODY"] && S.types.DEBRIS);
  }

  updateStatus() {
    if (!this.statusEl) return;
    const when = new Date(this.simTime()).toISOString().replace("T", " ").slice(0, 19);
    this.statusEl.textContent = `${S.shownCount.toLocaleString()} objects shown · ${when} UTC`;
  }

  fail(e) {
    S.error = String((e && e.stack) || e);
    if (this.statusEl) this.statusEl.textContent = "The globe could not load its data.";
    console.warn("SatTrack viewer:", S.error);
  }

  destroy() {
    this.destroyed = true;
    clearInterval(this.controller); clearInterval(this.statusTimer);
    if (this.worker) this.worker.terminate();
    if (this.widget && !this.widget.isDestroyed()) this.widget.destroy();
    S.ready = false;
  }
}

// Positions (km, Earth-fixed) of every object at one time, straight from the worker with no interpolation, for the
// parity test: [[satcat_id, x, y, z], ...]; NaN (null in JSON) for objects that fail.
S.snapshot = async (iso) => {
  if (!current || !current.ids) throw new Error("viewer not ready");
  const r = await current.call({ type: "compute", dates: [Date.parse(iso)], types: [] });
  const p = r.positions[0];
  return Array.from(current.ids, (id, i) => [id, p[3 * i], p[3 * i + 1], p[3 * i + 2]]);
};
S.setTypes = (types) => current && current.setTypes(types);
S.metrics = () => ({
  ready: S.ready, engine: S.engine, step: S.step, count: S.count, shown: S.shownCount, hiddenFailed: S.hiddenFailed,
  firstPositionsMs: S.firstPositionsMs, mainMsPerFrame: avg(S.applyMs), frameMs: avg(S.frameMs),
  workerMsPerPass: avg(S.workerMs), frames: S.frameMs.length, clockOffsetMs: S.clockOffsetMs,
});

// Called by the Dash bridge whenever the tracker page (re)renders its stores. A page re-render replaces div#globe,
// so a viewer whose container has left the document is destroyed and a new one mounted.
S.mount = (config, filters) => {
  S.filters = filters;   // the sidebar filter spec arrives here in roadmap 3.3
  const container = document.getElementById("globe");
  if (!container || !config) return "no-container";
  if (current && current.container === container) return "mounted";
  if (current) current.destroy();
  current = new Viewer(container, config);
  current.start().catch((e) => current && current.fail(e));
  return "mounting";
};

const bridge = window.sattrackViewerBridge;
if (bridge && bridge.config) S.mount(bridge.config, bridge.filters);
