// SatTrack Cesium viewer (roadmap 3.2; docs/cesium-architecture.md; decisions D-013 to D-029).
//
// Loaded only on the tracker page, and only when the viewer flag is on: the Dash clientside bridge
// (app/callbacks/callback_viewer.py) injects this module and calls mount() with the viewer-config store. It mounts
// Cesium into the empty div#globe, which no Dash callback ever writes to (D-013).
//
// - Positions come from static/viewer/worker.js, which propagates every shown object on a grid of simulation time;
//   this thread only interpolates linearly between the two samples around the current time (D-015). The grid step
//   adapts between 0.25 and 10 s of simulation time to the worker's speed, the frame rate and the play speed.
// - One PointPrimitiveCollection for every object, coloured by status (Active soft red, Inactive grey, from the design
//   tokens; no outline: owner, 24 Nov 2026). What is shown follows the page's filter spec (roadmap 3.3a): the panel's
//   controls, type switches included, write it to the filter-spec store, the Dash bridge hands it to mount(), and the
//   worker re-masks its records. Nothing is reloaded. UNKNOWN is never shown (D-011, D-016).
// - Natural Earth II from the self-hosted Cesium, no Cesium ion (D-014, D-022). SatTrack's credits replace
//   Cesium's credit display. Every data string is written with textContent.
// - The clock is corrected by the offset between this device and the server's Date header.
// - window.sattrackViewer exposes state and timings for the browser tests (parity and the D-027 budget).

const TYPES = ["PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"];
const TYPE_LABEL = { "PAYLOAD": "Payload", "ROCKET BODY": "Rocket body", "DEBRIS": "Debris" };
// Status colours come from the design tokens (assets/03_tokens.css), read when the points are made; the fallbacks are
// the same values, for a page without the app's stylesheet. "Colour by" (roadmap 3.13) adds the other palettes.
const STATUS_TOKENS = { active: ["--st-active", "#e8564a"], inactive: ["--st-inactive", "#7d8aa0"] };
const token = ([name, fallback]) =>
  (getComputedStyle(document.documentElement).getPropertyValue(name) || "").trim() || fallback;
const STEPS = [0.25, 0.5, 1, 2, 5, 10];     // seconds of simulation time between worker samples (D-015)
// D-052 (owner, 27 Nov 2026: laggy on a phone, first 30 s especially; filters slow; globe too light; dots too big):
// - The globe draws only when something changes: the camera moves, a filter applies, a label shows, or simulation
//   time moves on by RENDER_STEP_S (Cesium's request-render mode). At 1x that is 4 draws a second when nobody
//   touches it, instead of 30-60, which frees the page for the panel, taps and filters; moving or zooming draws
//   every frame as before. At whole-globe zoom a satellite moves well under a pixel between draws.
// - Darker Earth: the imagery dimmed (shade 2, chosen by the owner on a phone), no atmosphere glow, a navy base
//   colour so the globe isn't blank before its imagery arrives.
// - Dots 3 px, a little larger when zoomed in and smaller when zoomed out (scaleByDistance).
const RENDER_STEP_S = 0.25;
const EARTH_LOOK = { brightness: 0.55, contrast: 1.2, saturation: 0.8, gamma: 1.1 };
const GLOBE_BASE = ["--st-globe-base", "#0b1324"];
const DOT_PX = 3;
const BUSY_FRAME_MS = 200;                   // frames closer than this are continuous drawing (a gesture or fast play)
const LOAD_STEPS = ["Loading the globe…", "Downloading satellites…", "Placing satellites…", ""];
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
  shownCount: 0, hiddenFailed: 0, typeCounts: {}, matchCounts: {}, filters: null, filterChanges: 0,
  marks: {}, frameMs: [], busyFrameMs: [], applyMs: [], workerMs: [], hint: null, label: null,
  // Per applied filter change (roadmap 3.3b budget test): when it was applied (performance.now()), the time from the
  // spec reaching the viewer to the points updated, and the main-thread part of that (showing/hiding and resampling).
  filterReceivedAt: 0, filterAppliedAt: 0, filterMs: [], filterMainMs: [],
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
    this.loadStep = 0;
  }

  // The loading bar (D-052): the page renders it inside div#globe (viz_globe.py) so it shows before any script runs;
  // each start-up step fills one more bar, and the last hides it.
  stage(n) {
    if (n <= this.loadStep) return;
    this.loadStep = n;
    const box = this.container.querySelector(".sattrack-loading");
    if (!box) return;
    box.querySelectorAll(".sattrack-loading-bar").forEach((b, i) => b.classList.toggle("is-done", i < n));
    const text = box.querySelector(".sattrack-loading-text");
    if (text) text.textContent = LOAD_STEPS[Math.min(n, LOAD_STEPS.length - 1)];
    if (n >= LOAD_STEPS.length) box.classList.add("is-done");
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
    this.spec = S.filters;   // the page's starting spec, rendered into the store: masked before the first samples
    this.worker.postMessage({ type: "init", data: this.config.data, satellite: this.config.satellite,
                              filterSpec: this.config.filterSpec, rules: this.config.specRules, spec: this.spec,
                              first: { dates: [t0, t0 + 1000] } });
    const clock = serverClock(this.config.data);

    this.stage(1);
    const Cesium = await loadCesium(this.config);
    S.marks.cesium = performance.now();
    this.stage(2);
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
    const scene = this.widget.scene;
    scene.requestRenderMode = true;
    scene.maximumRenderTimeChange = RENDER_STEP_S;
    scene.globe.baseColor = Cesium.Color.fromCssColorString(token(GLOBE_BASE));
    scene.globe.showGroundAtmosphere = false;
    if (scene.skyAtmosphere) scene.skyAtmosphere.show = false;
    const darken = (layer) => Object.assign(layer, EARTH_LOOK);
    for (let i = 0; i < scene.imageryLayers.length; i++) darken(scene.imageryLayers.get(i));
    scene.imageryLayers.layerAdded.addEventListener(darken);
    S.webgl = (() => { try { const gl = this.widget.scene.context._gl, ext = gl.getExtension("WEBGL_debug_renderer_info");
      return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); } catch (e) { return null; } })();
    S.marks.viewer = performance.now();

    const m = await meta;
    S.marks.data = performance.now();
    this.stage(3);
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
    const colours = [token(STATUS_TOKENS.inactive), token(STATUS_TOKENS.active)].map((c) => Cesium.Color.fromCssColorString(c));
    S.colours = { active: token(STATUS_TOKENS.active), inactive: token(STATUS_TOKENS.inactive) };
    const bySize = new Cesium.NearFarScalar(1.0e7, 1.2, 6.0e7, 0.7);   // metres from the camera -> size factor
    this.handles = Array.from(m.active, (a, i) => this.points.add({
      position: Cesium.Cartesian3.ZERO, show: false, pixelSize: DOT_PX, color: colours[a], outlineWidth: 0,
      scaleByDistance: bySize, id: i,   // id: the record index, for hover labels
    }));
    this.mask = new Uint8Array(this.typeCodes.length);
    this.buildPanel();

    // First positions: the two samples computed with "ready", then one sample ahead always in flight.
    const init = await ready;
    if (this.destroyed) return;
    S.engine = `worker-${init.engine}`;
    S.builtBeforeReady = init.built;   // records built before the first positions (D-042)
    S.failed = init.failed;
    this.mask = init.mask;
    S.matchCounts = init.counts;
    if (init.specError) console.warn("SatTrack viewer: filter spec rejected:", init.specError);
    this.workerReady = true;
    // A spec that changed while the worker was starting (the page's filters moved during load)
    if (JSON.stringify(S.filters) !== JSON.stringify(this.spec)) this.setFilters(S.filters);
    push(S.workerMs, init.first.ms / 2);
    [this.a, this.b] = init.first.dates.map((t, i) => ({ t, pos: init.first.positions[i] }));
    this.c = null;
    this.requestNext();
    this.apply(this.simTime());
    scene.requestRender();
    S.marks.firstPositions = performance.now();
    this.stage(4);
    this.labels();
    S.firstPositionsMs = S.marks.firstPositions - S.marks.start;
    this.lastFrame = performance.now();
    this.widget.scene.preRender.addEventListener(() => this.frame());
    this.controller = setInterval(() => this.adapt(), 2000);
    this.statusTimer = setInterval(() => this.updateStatus(), 1000);
    S.ready = true;
    this.updateStatus();
  }

  simTime() { return this.Cesium.JulianDate.toDate(this.widget.clock.currentTime).getTime(); }

  async sample(ms) {
    const r = await this.call({ type: "compute", dates: [ms] });
    push(S.workerMs, r.ms);
    return { t: ms, pos: r.positions[0] };
  }

  requestNext() {
    const nt = this.b.t + this.step * 1000, gen = this.gen;
    this.sample(nt).then((r) => { if (gen === this.gen) this.c = r; }).catch((e) => this.fail(e));
  }

  frame() {
    const now = performance.now();
    push(S.frameMs, now - this.lastFrame);
    if (now - this.lastFrame < BUSY_FRAME_MS) push(S.busyFrameMs, now - this.lastFrame);
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

  // Interpolate between samples a and b and move the points (metres). Objects outside the filter mask, and failed
  // objects (NaN in either sample), are hidden.
  apply(t) {
    const { a, b, handles, mask } = this;
    const f = b.t > a.t ? Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t))) : 0;
    const scratch = this.scratch || (this.scratch = new this.Cesium.Cartesian3());
    let shown = 0, bad = 0;
    for (let i = 0; i < handles.length; i++) {
      const h = handles[i];
      if (!mask[i]) { if (h.show) h.show = false; continue; }
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
    // Frame times only from continuous drawing (a gesture or fast play): between draws the globe idles (D-052)
    const w = avg(S.workerMs.slice(-5)), frame = avg(S.busyFrameMs.slice(-60));
    const speed = Math.abs(this.widget.clock.multiplier) || 1;
    let wallS = Math.max(1, (4 * w) / 1000);
    if (frame > 50) wallS *= 2;
    const want = speed * wallS;
    const step = STEPS.find((s) => s >= want) || STEPS[STEPS.length - 1];
    if (step !== this.step) { this.step = S.step = step; }
    // D-027: suggest switching debris off when junk mode runs below 20 fps for 5 s; never do it automatically.
    const slow = (S.matchCounts.DEBRIS || 0) > 0 && S.busyFrameMs.length > 60 && avg(S.busyFrameMs.slice(-150)) > 50;
    S.hint = slow ? "Running slowly: switching debris off makes the globe smoother." : null;
    if (this.hintEl) this.hintEl.textContent = S.hint || "";
  }

  // A new filter spec from the page (roadmap 3.3a): the worker re-masks its records (no reload, same worker), then
  // the points are resampled at once so newly shown objects don't wait a step.
  async setFilters(spec) {
    S.filters = spec;
    if (!this.workerReady) return;   // the spec is picked up when the worker is ready
    const gen = this.filterGen = (this.filterGen || 0) + 1;
    const t0 = S.filterReceivedAt = performance.now();
    try {
      const r = await this.call({ type: "filter", spec });
      if (gen !== this.filterGen || this.destroyed) return;   // a newer spec is on its way
      const t1 = performance.now();
      this.spec = spec;
      this.mask = r.mask;
      S.matchCounts = r.counts;
      this.apply(this.simTime());
      const main = performance.now() - t1;
      // Newly shown objects get positions from a fresh pair of samples; the change counts as applied once they have them.
      if (this.a) await this.resync(this.simTime());
      if (gen !== this.filterGen || this.destroyed) return;
      this.apply(this.simTime());   // show them now rather than on the next frame
      this.widget.scene.requestRender();
      const t2 = performance.now();
      push(S.filterMs, t2 - t0);
      push(S.filterMainMs, main);
      S.filterAppliedAt = t2;
      S.filterChanges++;
    } catch (e) { console.warn("SatTrack viewer: filter not applied:", String(e)); }
  }

  // Hover labels (D-052, pulled forward from roadmap 3.4's first tier): pointing at a dot shows its name, SATCAT
  // number, type, status, orbit class and launch year; on a touch screen a tap shows it and a tap elsewhere hides it.
  // Picking is throttled (one pick per 100 ms) and skipped while dragging; the label hides when the camera moves.
  // The details come from the worker's records; every string goes in with textContent.
  labels() {
    const Cesium = this.Cesium, scene = this.widget.scene;
    const label = this.labelEl = el("div", "sattrack-viewer-label");
    label.hidden = true;
    label.setAttribute("role", "status");
    this.container.append(label);
    const handler = this.handler = new Cesium.ScreenSpaceEventHandler(scene.canvas);
    let pending = null, timer = null, dragging = false, shownIndex = null;
    const hide = () => { label.hidden = true; shownIndex = null; S.label = null; };
    const show = async (pos) => {
      const picked = scene.pick(pos);
      const i = picked && picked.collection === this.points && Number.isInteger(picked.id) ? picked.id : null;
      if (i === null || !this.mask[i]) { hide(); return; }
      if (i === shownIndex) { place(pos); return; }
      shownIndex = i;
      const info = await this.call({ type: "info", index: i });
      if (shownIndex !== i || this.destroyed) return;
      const r = info.record;
      label.textContent = "";
      const name = r.object_name === "TBA - TO BE ASSIGNED"   // Space-Track's "not yet named"
        ? `Not yet named${r.object_id ? ` (${r.object_id})` : ""}` : (r.object_name || "(no name)");
      label.append(el("strong", null, name),
                   el("div", null, [`SATCAT ${r.satcat_id}`, TYPE_LABEL[r.object_type] || "Unknown type",
                                    r.operational_status].filter(Boolean).join(" · ")),
                   el("div", null, [r.orbit_class, r.launch_year ? `launched ${r.launch_year}` : null,
                                    r.owner_country].filter(Boolean).join(" · ")));
      place(pos);
      label.hidden = false;
      S.label = { satcat_id: r.satcat_id, object_name: r.object_name };
    };
    const place = (pos) => {
      const w = this.container.clientWidth;
      label.style.left = `${Math.min(pos.x + 12, w - 220)}px`;
      label.style.top = `${Math.max(pos.y - 12, 4)}px`;
    };
    handler.setInputAction(() => { dragging = true; hide(); }, Cesium.ScreenSpaceEventType.LEFT_DOWN);
    handler.setInputAction(() => { dragging = false; }, Cesium.ScreenSpaceEventType.LEFT_UP);
    handler.setInputAction((m) => {
      if (dragging) return;
      pending = m.endPosition;
      if (timer) return;
      timer = setTimeout(() => { timer = null; if (pending) show(pending).catch(hide); }, 100);
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    handler.setInputAction((c) => { show(c.position).catch(hide); }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    scene.camera.moveStart.addEventListener(hide);
    // For the browser tests: point at a canvas position; where an object is on the canvas (null if not shown)
    S.pointAt = (x, y) => show(new Cesium.Cartesian2(x, y));
    S.screenOf = (satcatId) => {
      const i = Array.prototype.indexOf.call(this.ids, satcatId);
      if (i < 0 || !this.mask[i] || !this.handles[i].show) return null;
      const w = Cesium.SceneTransforms.worldToWindowCoordinates(scene, this.handles[i].position);
      return w ? { x: w.x, y: w.y } : null;
    };
  }

  // The overlay keeps the status line, the slow-device hint and the credits; the type switches are in the page's
  // filter panel since roadmap 3.3a.
  buildPanel() {
    const panel = el("div", "sattrack-viewer-panel");
    panel.setAttribute("aria-label", "Globe status");
    this.statusEl = el("div", "sattrack-viewer-status", "Loading…");
    this.hintEl = el("div", "sattrack-viewer-hint");
    const credits = el("div", "sattrack-viewer-credits");
    for (const [before, name, href, after] of CREDITS) {
      const line = el("div"), link = el("a", null, name);
      link.href = href; link.target = "_blank"; link.rel = "noopener noreferrer";
      line.append(document.createTextNode(before), link, document.createTextNode(after));
      credits.append(line);
    }
    panel.append(this.statusEl, this.hintEl);
    this.container.append(panel, credits);
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
    if (this.handler && !this.handler.isDestroyed()) this.handler.destroy();
    if (this.worker) this.worker.terminate();
    if (this.widget && !this.widget.isDestroyed()) this.widget.destroy();
    S.ready = false;
  }
}

// Positions (km, Earth-fixed) of every object at one time, straight from the worker with no interpolation, for the
// parity test: [[satcat_id, x, y, z], ...]; NaN (null in JSON) for objects that fail.
S.snapshot = async (iso) => {
  if (!current || !current.ids) throw new Error("viewer not ready");
  const r = await current.call({ type: "compute", dates: [Date.parse(iso)], all: true });
  const p = r.positions[0];
  return Array.from(current.ids, (id, i) => [id, p[3 * i], p[3 * i + 1], p[3 * i + 2]]);
};
// The satcat_ids shown now (in the mask and placed), for the browser tests' exact-id checks.
S.shownIds = () => {
  if (!current || !current.handles) return [];
  return Array.from(current.ids).filter((id, i) => current.mask[i] && current.handles[i].show);
};
S.metrics = () => ({
  ready: S.ready, engine: S.engine, step: S.step, count: S.count, shown: S.shownCount, hiddenFailed: S.hiddenFailed,
  firstPositionsMs: S.firstPositionsMs, mainMsPerFrame: avg(S.applyMs), frameMs: avg(S.frameMs),
  workerMsPerPass: avg(S.workerMs), frames: S.frameMs.length, clockOffsetMs: S.clockOffsetMs,
});

// Called by the Dash bridge whenever the tracker page (re)renders its stores. A page re-render replaces div#globe,
// so a viewer whose container has left the document is destroyed and a new one mounted.
S.mount = (config, filters) => {
  const container = document.getElementById("globe");
  if (!container || !config) { S.filters = filters; return "no-container"; }
  if (current && current.container === container) {
    if (JSON.stringify(filters) !== JSON.stringify(S.filters)) current.setFilters(filters);
    return "mounted";
  }
  S.filters = filters;
  if (current) current.destroy();
  current = new Viewer(container, config);
  current.start().catch((e) => current && current.fail(e));
  return "mounting";
};

const bridge = window.sattrackViewerBridge;
if (bridge && bridge.config) S.mount(bridge.config, bridge.filters);
