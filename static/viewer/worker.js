// SatTrack viewer: propagation Web Worker (roadmap 3.2; decisions D-015, D-029; docs/cesium-architecture.md).
//
// Loads /data/objects.json itself (D-009: the browser builds its records on load, in a worker), builds one
// satellite.js record per object from the OMM fields, and answers compute requests with Earth-fixed positions in km.
// The engine sits behind compute(dates, active) -> positions so the WASM BulkPropagator (roadmap 3.11) can replace
// the JavaScript propagate() without touching the main thread. Failed objects are NaN, never (0, 0, 0).
//
// Messages in:  {type: "init", data, satellite, first: {dates, types}}  data URL, satellite.js base URL (same
//                                                                       origin), the first samples to compute
//               {type: "compute", id, dates: [ms...], types: [code...]} codes index TYPES; [] or omitted = all
// Messages out: {type: "meta", count, ids, types, generatedAt}           as soon as the data is parsed
//               {type: "ready", failed, engine, first: {dates, positions, ms}}  shown types' records built
//               {type: "records", failed}                               every record built (all failures)
//               {type: "positions", id, dates, positions: [Float64Array...], ms}  (buffers transferred)
//               {type: "error", id, error}

const TYPES = ["PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"];
let engine = null;

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

// The JavaScript engine (D-029): satellite.js propagate() per object, rotated to Earth-fixed with GMST.
function jsEngine(sat, satrecs, typeCodes) {
  return {
    name: "js",
    compute(dates, types) {
      const want = types && types.length ? new Set(types) : null;
      return dates.map((ms) => {
        const date = new Date(ms), gmst = sat.gstime(date), out = new Float64Array(3 * satrecs.length).fill(NaN);
        for (let i = 0; i < satrecs.length; i++) {
          const s = satrecs[i];
          if (!s || (want && !want.has(typeCodes[i]))) continue;
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

async function init({ data, satellite, first }) {
  // Only the modules the JavaScript engine needs (no WebAssembly, so no 'wasm-unsafe-eval' in the CSP).
  const [io, prop, tf, response] = await Promise.all([
    import(`${satellite}dist/io.js`), import(`${satellite}dist/propagation.js`), import(`${satellite}dist/transforms.js`),
    fetch(data),
  ]);
  const sat = { json2satrec: io.json2satrec, propagate: prop.propagate, gstime: prop.gstime, eciToEcf: tf.eciToEcf };
  if (!response.ok) throw new Error(`${data}: HTTP ${response.status}`);
  const dataset = await response.json();
  const records = Array.isArray(dataset.records) ? dataset.records : [];
  const ids = new Int32Array(records.length), types = new Uint8Array(records.length), satrecs = new Array(records.length);
  records.forEach((r, i) => {
    ids[i] = Number(r.satcat_id);
    const code = TYPES.indexOf(r.object_type);
    types[i] = code < 0 ? TYPES.indexOf("UNKNOWN") : code;
  });
  // The main thread creates its points from this while the records are built.
  self.postMessage({ type: "meta", count: records.length, ids: ids.slice(), types: types.slice(),
                     generatedAt: typeof dataset.generated_at === "string" ? dataset.generated_at : null });
  const failed = [];
  const build = (keep) => records.forEach((r, i) => {
    if (!keep(types[i])) return;
    let s = null;
    try {
      s = sat.json2satrec(toOmm(r));
      if (!s || s.error) s = null;
    } catch (e) { s = null; }
    if (!s) failed.push(ids[i]);
    satrecs[i] = s;
  });
  // Records for the shown types first, then the first samples (sent with "ready", saving a round trip), then the
  // other types' records, so hidden debris doesn't delay the first positions. Compute requests wait until done.
  const shown = new Set(first.types);
  build((t) => shown.has(t));
  engine = jsEngine(sat, satrecs, types);
  const t0 = performance.now();
  const positions = engine.compute(first.dates, first.types);
  self.postMessage({ type: "ready", engine: engine.name, failed: failed.slice(),
                     first: { dates: first.dates, positions, ms: performance.now() - t0 } },
                   positions.map((p) => p.buffer));
  build((t) => !shown.has(t));
  self.postMessage({ type: "records", failed });
}

self.onmessage = async ({ data: msg }) => {
  try {
    if (msg.type === "init") {
      await init(msg);
      return;
    }
    if (msg.type === "compute") {
      if (!engine) throw new Error("compute before init");
      const t0 = performance.now();
      const positions = engine.compute(msg.dates, msg.types);
      self.postMessage({ type: "positions", id: msg.id, dates: msg.dates, positions, ms: performance.now() - t0 },
                       positions.map((p) => p.buffer));
    }
  } catch (e) {
    self.postMessage({ type: "error", id: msg && msg.id, error: String((e && e.stack) || e) });
  }
};
