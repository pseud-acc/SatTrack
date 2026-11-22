// Cesium spike (roadmap 3.1): propagation in a Web Worker, for index.html?engine=worker.
// The worker fetches and parses /data/objects.json itself, keeps the satrecs, and answers {id, t} (ms since epoch)
// with Earth-fixed positions in km as a transferred Float64Array ([x0, y0, z0, x1, ...]; NaN = failed).
import * as satellite from "https://cdn.jsdelivr.net/npm/satellite.js@7.1.0/dist/index.js";
// Import maps don't apply inside workers, so createSingleThreadRuntime()'s import('#wasm-single-thread') can't
// resolve here: load the WASM module and the runtime factory by their real paths instead.
import { createSingleThreadRuntimeFromModule } from
  "https://cdn.jsdelivr.net/npm/satellite.js@7.1.0/dist/wasm/runtimes/single-thread-runtime.js";
import createWasmModule from "https://cdn.jsdelivr.net/npm/satellite.js@7.1.0/wasm-build/base-release/index.js";

const toOmm = (r) => ({
  OBJECT_NAME: r.object_name, OBJECT_ID: r.object_id, NORAD_CAT_ID: r.satcat_id, EPOCH: r.epoch,
  MEAN_MOTION: r.mean_motion, ECCENTRICITY: r.eccentricity, INCLINATION: r.inclination,
  RA_OF_ASC_NODE: r.ra_of_asc_node, ARG_OF_PERICENTER: r.arg_of_pericenter, MEAN_ANOMALY: r.mean_anomaly,
  EPHEMERIS_TYPE: r.ephemeris_type, CLASSIFICATION_TYPE: r.classification_type, ELEMENT_SET_NO: r.element_set_no,
  REV_AT_EPOCH: r.rev_at_epoch, BSTAR: r.bstar, MEAN_MOTION_DOT: r.mean_motion_dot,
  MEAN_MOTION_DDOT: r.mean_motion_ddot,
});

let satrecs = [], compute = null;

async function init({ types, engine }) {
  const wanted = new Set(types);
  const dataset = await (await fetch("/data/objects.json")).json();
  const meta = [];
  let failed = 0;
  for (const r of dataset.records) {
    if (!wanted.has(r.object_type)) continue;
    try {
      const s = satellite.json2satrec(toOmm(r));
      if (s.error) { failed++; continue; }
      satrecs.push(s); meta.push([r.satcat_id, r.object_type]);
    } catch (e) { failed++; }
  }
  if (engine === "wasm") {
    const runtime = await createSingleThreadRuntimeFromModule(await createWasmModule());
    const bulk = new satellite.BulkPropagator({
      runtime, satRecsCount: satrecs.length, datesCount: 1,
      calculators: [new satellite.EciBaseCalculator(), new satellite.GmstCalculator(),
                    new satellite.EcfPositionCalculator()],
    });
    bulk.setSatRecs(satrecs);
    compute = async (date) => {
      bulk.setDates([date]);
      await bulk.run();
      return Float64Array.from(bulk.getRawOutput().ecfPosition);
    };
  } else {
    compute = async (date) => {
      const out = new Float64Array(3 * satrecs.length), gmst = satellite.gstime(date);
      for (let i = 0; i < satrecs.length; i++) {
        const pv = satellite.propagate(satrecs[i], date);
        const p = pv && pv.position ? satellite.eciToEcf(pv.position, gmst) : { x: NaN, y: NaN, z: NaN };
        out[3 * i] = p.x; out[3 * i + 1] = p.y; out[3 * i + 2] = p.z;
      }
      return out;
    };
  }
  return { meta, failed };
}

self.onmessage = async ({ data }) => {
  try {
    if (data.init) {
      const r = await init(data.init);
      self.postMessage({ ready: true, ...r });
      return;
    }
    const t0 = performance.now();
    const pos = await compute(new Date(data.t));
    self.postMessage({ id: data.id, t: data.t, pos, ms: performance.now() - t0 }, [pos.buffer]);
  } catch (e) {
    self.postMessage({ error: String(e && e.stack || e) });
  }
};
