// SatTrack viewer: propagation Web Worker (roadmap 3.2, 3.3a; decisions D-015, D-029; docs/cesium-architecture.md).
//
// Loads /data/objects.json itself (D-009: the browser builds its records on load, in a worker), builds one
// satellite.js record per object from the OMM fields, and answers compute requests with Earth-fixed positions in km.
// The engine sits behind compute(dates) -> positions so the WASM BulkPropagator (roadmap 3.11) can replace the
// JavaScript propagate() without touching the main thread. Failed objects are NaN, never (0, 0, 0).
//
// Filtering (roadmap 3.3a): the worker keeps each object's filterable fields (D-033) and turns the page's filter spec
// into a mask with static/viewer/filter_spec.js (the browser's implementation, held to the shared conformance cases,
// D-034). Only masked-in objects are propagated. A new spec never reloads the data or recreates the worker.
//
// Messages in:  {type: "init", data, satellite, filterSpec, rules, spec, first: {dates}}
//                 data URL, satellite.js base URL and filter_spec.js URL (same origin), the spec rules, the page's
//                 starting spec (null: nothing shown), the first samples to compute
//               {type: "filter", id, spec}                        a new spec: returns the mask and the counts
//               {type: "compute", id, dates: [ms...], all}         all: true propagates every object (parity test)
// Messages out: {type: "meta", count, ids, types, active, generatedAt}  as soon as the data is parsed
//               {type: "ready", failed, engine, built, mask, counts, first: {dates, positions, ms}}
//                 records of the masked-in types built (built: how many, for the start-up check, D-042)
//               {type: "records", failed}                         every record built (all failures)
//               {type: "filtered", id, mask, counts}              (mask transferred)
//               {type: "positions", id, dates, positions: [Float64Array...], ms}  (buffers transferred)
//               {type: "error", id, error}

const TYPES = ["PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"];
const FIELDS = ["satcat_id", "object_name", "object_type", "operational_status", "orbit_class", "owner_country",
                "launch_vehicle_brand", "mission_category_labels", "launch_year"];
let engine = null, spec = null, rows = null, types = null, mask = null;

// The record's field names are the warehouse's (D-009, D-010); satellite.js takes the CCSDS OMM keywords, which are
// the same names upper-cased.
const toOmm = (r) => ({
  OBJECT_NAME: r.object_name, OBJECT_ID: r.object_id, NORAD_CAT_ID: r.satcat_id, EPOCH: r.epoch,
  MEAN_MOTION: r.mean_motion, ECCENTRICITY: r.eccentricity, INCLINATION: r.inclination,
  RA_OF_ASC_NODE: r.ra_of_asc_node, ARG_OF_PERICENTER: r.arg_of_pericenter, MEAN_ANOMALY: r.mean_anomaly,
  EPHEMERIS_TYPE: r.ephemeris_type, CLASSIFICATION_TYPE: r.classification_type, ELEMENT_SET_NO: r.element_set_no,
  REV_AT_EPOCH: r.rev_at_epoch, BSTAR: r.bstar, MEAN_MOTION_DOT: r.mean_motion_dot,
  MEAN_MOTION_DDOT: r.mean_motion_ddot,
});

// The mask for a spec (1 = shown) and the matched count per type. A null spec, or one the rules reject, shows
// nothing; a rejected spec is also reported, since the server validated it first (D-031) and it should never happen.
function buildMask(next) {
  const m = new Uint8Array(rows.length), counts = Object.fromEntries(TYPES.map((t) => [t, 0]));
  if (next) {
    const test = spec.compile(next, spec.rules);
    for (let i = 0; i < rows.length; i++) {
      if (types[i] !== 3 && test(rows[i])) { m[i] = 1; counts[TYPES[types[i]]]++; }   // UNKNOWN never shown (D-011)
    }
  }
  return { mask: m, counts };
}

// The JavaScript engine (D-029): satellite.js propagate() per object, rotated to Earth-fixed with GMST. Objects
// outside the current mask are skipped (NaN), unless `all` is asked for.
function jsEngine(sat, satrecs) {
  return {
    name: "js",
    compute(dates, all) {
      return dates.map((ms) => {
        const date = new Date(ms), gmst = sat.gstime(date), out = new Float64Array(3 * satrecs.length).fill(NaN);
        for (let i = 0; i < satrecs.length; i++) {
          const s = satrecs[i];
          if (!s || (!all && !mask[i])) continue;
          let p = null;
          try {
            const pv = sat.propagate(s, date);
            p = pv && pv.position ? sat.eciToEcf(pv.position, gmst) : null;
          } catch (e) { p = null; }
          if (p && Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z)) {
            out[3 * i] = p.x; out[3 * i + 1] = p.y; out[3 * i + 2] = p.z;
          }
        }
        return out;
      });
    },
  };
}

async function init({ data, satellite, filterSpec, rules, spec: startSpec, first }) {
  // Only the modules the JavaScript engine needs (no WebAssembly, so no 'wasm-unsafe-eval' in the CSP).
  const [io, prop, tf, fs, response] = await Promise.all([
    import(`${satellite}dist/io.js`), import(`${satellite}dist/propagation.js`), import(`${satellite}dist/transforms.js`),
    import(filterSpec), fetch(data),
  ]);
  const sat = { json2satrec: io.json2satrec, propagate: prop.propagate, gstime: prop.gstime, eciToEcf: tf.eciToEcf };
  spec = { compile: fs.compile, rules };
  if (!response.ok) throw new Error(`${data}: HTTP ${response.status}`);
  const dataset = await response.json();
  const records = Array.isArray(dataset.records) ? dataset.records : [];
  const ids = new Int32Array(records.length), active = new Uint8Array(records.length), satrecs = new Array(records.length);
  types = new Uint8Array(records.length);
  rows = new Array(records.length);
  records.forEach((r, i) => {
    ids[i] = Number(r.satcat_id);
    const code = TYPES.indexOf(r.object_type);
    types[i] = code < 0 ? TYPES.indexOf("UNKNOWN") : code;
    active[i] = r.operational_status === "Active" ? 1 : 0;
    const row = {};
    for (const f of FIELDS) row[f] = r[f] === undefined ? null : r[f];
    rows[i] = row;
  });
  let filtered = { mask: new Uint8Array(records.length), counts: {} };
  let specError = null;
  try { filtered = buildMask(startSpec); } catch (e) { specError = String(e); }
  mask = filtered.mask;
  // The main thread creates its points from this while the records are built.
  self.postMessage({ type: "meta", count: records.length, ids: ids.slice(), types: types.slice(), active,
                     generatedAt: typeof dataset.generated_at === "string" ? dataset.generated_at : null });
  const failed = [];
  let built = 0;
  const build = (keep) => records.forEach((r, i) => {
    if (satrecs[i] !== undefined || !keep(i)) return;
    built++;
    let s = null;
    try {
      s = sat.json2satrec(toOmm(r));
      if (!s || s.error) s = null;
    } catch (e) { s = null; }
    if (!s) failed.push(ids[i]);
    satrecs[i] = s;
  });
  // Records of the types the spec shows first, then the first samples (sent with "ready", saving a round trip), then
  // the other types' records, so hidden debris doesn't delay the first positions (D-042: with the default spec,
  // records built before the first positions == the payload count). Compute requests wait until done.
  const shownTypes = new Set();
  for (let i = 0; i < mask.length; i++) if (mask[i]) shownTypes.add(types[i]);
  build((i) => shownTypes.has(types[i]));
  engine = jsEngine(sat, satrecs);
  const t0 = performance.now();
  const positions = engine.compute(first.dates, false);
  const sentMask = mask.slice();
  self.postMessage({ type: "ready", engine: engine.name, failed: failed.slice(), built, mask: sentMask,
                     counts: filtered.counts, specError,
                     first: { dates: first.dates, positions, ms: performance.now() - t0 } },
                   [...positions.map((p) => p.buffer), sentMask.buffer]);
  build(() => true);
  self.postMessage({ type: "records", failed });
}

self.onmessage = async ({ data: msg }) => {
  try {
    if (msg.type === "init") {
      await init(msg);
      return;
    }
    if (!engine) throw new Error(`${msg.type} before init`);
    if (msg.type === "filter") {
      const next = buildMask(msg.spec);   // throws InvalidSpec for a bad spec: reported, the old mask stays
      mask = next.mask;
      const sent = mask.slice();
      self.postMessage({ type: "filtered", id: msg.id, mask: sent, counts: next.counts }, [sent.buffer]);
      return;
    }
    if (msg.type === "compute") {
      const t0 = performance.now();
      const positions = engine.compute(msg.dates, !!msg.all);
      self.postMessage({ type: "positions", id: msg.id, dates: msg.dates, positions, ms: performance.now() - t0 },
                       positions.map((p) => p.buffer));
    }
  } catch (e) {
    self.postMessage({ type: "error", id: msg && msg.id, error: String((e && e.stack) || e) });
  }
};
