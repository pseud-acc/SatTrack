// SatTrack filter spec in the browser (roadmap 3.3a; D-030 to D-034). The same rules as app/core/filter_spec.py, run
// in the viewer's worker to show or hide objects without asking the server. Both implementations pass the shared cases
// in tests/contracts/filter_spec_cases.json (tests/e2e/test_filter_spec_browser.py runs this file in Chromium).
//
// `rules` comes from the server (app.core.filter_spec.browser_rules(), in the viewer config): the schema's version,
// clause limit and, for every allowed field, its kind and the JSON Schema of each operator's value, taken from the
// generated app/contracts/filter_spec.schema.json, so nothing here is copied by hand. The validator understands only
// the keywords that schema uses (type, enum, const, min/maxLength, min/maxItems, uniqueItems, items, anyOf,
// properties, required, additionalProperties) and rejects anything it doesn't recognise.
//
// Missing values are explicit (D-032): a scalar is missing when null; a list field when null or empty.
//   eq never matches missing; in matches missing only when null is listed; not_in is the exact complement of in;
//   between matches missing only with include_missing; contains_any matches a missing list only when null is listed;
//   is_missing true selects missing, false present.
// No imports, no eval: it runs under the viewer's Content Security Policy (D-041).

export class InvalidSpec extends Error {}

const isObj = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const KNOWN = new Set(["type", "enum", "const", "minLength", "maxLength", "minItems", "maxItems", "uniqueItems",
  "items", "anyOf", "properties", "required", "additionalProperties", "default", "description", "title"]);

function typeOk(type, v) {
  switch (type) {
    case "null": return v === null;
    case "boolean": return typeof v === "boolean";
    case "string": return typeof v === "string";
    case "integer": return typeof v === "number" && Number.isInteger(v);
    case "number": return typeof v === "number" && Number.isFinite(v);
    case "array": return Array.isArray(v);
    case "object": return isObj(v);
    default: return false;
  }
}

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// True when v satisfies the (subset) JSON Schema s.
export function conforms(s, v) {
  for (const k of Object.keys(s)) if (!KNOWN.has(k)) return false;   // an unknown keyword: refuse, never guess
  if (s.type !== undefined) {
    const types = Array.isArray(s.type) ? s.type : [s.type];
    if (!types.some((t) => typeOk(t, v))) return false;
  }
  if (s.const !== undefined && !same(s.const, v)) return false;
  if (s.enum !== undefined && !s.enum.some((e) => same(e, v))) return false;
  if (typeof v === "string") {
    if (s.minLength !== undefined && [...v].length < s.minLength) return false;
    if (s.maxLength !== undefined && [...v].length > s.maxLength) return false;
  }
  if (Array.isArray(v)) {
    if (s.minItems !== undefined && v.length < s.minItems) return false;
    if (s.maxItems !== undefined && v.length > s.maxItems) return false;
    if (s.uniqueItems && new Set(v.map((x) => JSON.stringify(x))).size !== v.length) return false;
    if (s.items !== undefined && !v.every((x) => conforms(s.items, x))) return false;
  }
  if (isObj(v)) {
    for (const r of s.required || []) if (!(r in v)) return false;
    const props = s.properties || {};
    for (const [k, x] of Object.entries(v)) {
      if (k in props) { if (!conforms(props[k], x)) return false; }
      else if (s.additionalProperties === false) return false;
    }
  }
  if (s.anyOf !== undefined && !s.anyOf.some((a) => conforms(a, v))) return false;
  return true;
}

// Return the spec if it is valid under `rules`, else throw InvalidSpec (naming the clause, never echoing values).
export function validate(spec, rules) {
  if (!isObj(spec)) throw new InvalidSpec("invalid filter spec at spec");
  for (const k of Object.keys(spec)) if (k !== "version" && k !== "clauses") throw new InvalidSpec("invalid filter spec at spec");
  if (spec.version !== rules.version) throw new InvalidSpec("invalid filter spec at version");
  if (!Array.isArray(spec.clauses) || spec.clauses.length > rules.maxClauses) throw new InvalidSpec("invalid filter spec at clauses");
  spec.clauses.forEach((c, i) => {
    const where = `invalid filter spec at clauses/${i}`;
    if (!isObj(c) || Object.keys(c).length !== 3 || !("field" in c) || !("op" in c) || !("value" in c)) throw new InvalidSpec(where);
    const field = typeof c.field === "string" && Object.prototype.hasOwnProperty.call(rules.fields, c.field) ? rules.fields[c.field] : null;
    const valueSchema = field && typeof c.op === "string" && Object.prototype.hasOwnProperty.call(field.ops, c.op) ? field.ops[c.op] : null;
    if (!valueSchema || !conforms(valueSchema, c.value)) throw new InvalidSpec(where);
  });
  return spec;
}

const missingScalar = (v) => v === null || v === undefined;
const missingList = (v) => v === null || v === undefined || (Array.isArray(v) && v.length === 0);

// A per-record test for one clause; `kind` is the field's kind ("string_list" for list fields).
function clauseTest(clause, kind) {
  const { field, op, value } = clause;
  if (kind === "string_list") {
    if (op === "is_missing") return (r) => missingList(r[field]) === value;
    const wanted = new Set(value.filter((v) => v !== null)), nullOk = value.includes(null);
    return (r) => { const v = r[field];
      return missingList(v) ? nullOk : v.some((x) => wanted.has(x)); };
  }
  if (op === "is_missing") return (r) => missingScalar(r[field]) === value;
  if (op === "eq") return (r) => !missingScalar(r[field]) && r[field] === value;
  if (op === "in" || op === "not_in") {
    const present = new Set(value.filter((v) => v !== null)), nullOk = value.includes(null);
    const inside = (r) => (missingScalar(r[field]) ? nullOk : present.has(r[field]));
    return op === "in" ? inside : (r) => !inside(r);
  }
  if (op === "between") {
    const incl = !!value.include_missing;
    return (r) => { const v = r[field];
      return missingScalar(v) ? incl : v >= value.min && v <= value.max; };
  }
  throw new InvalidSpec(`unknown op ${op}`);   // unreachable after validate()
}

// A function record -> boolean for a valid spec (validates first). Every clause must hold (AND).
export function compile(spec, rules) {
  validate(spec, rules);
  const tests = spec.clauses.map((c) => clauseTest(c, rules.fields[c.field].kind));
  return (r) => tests.every((t) => t(r));
}

// The keys of the records the spec selects, in record order: the shape the conformance cases check.
export function selectIds(spec, records, rules, key = "satcat_id") {
  const test = compile(spec, rules);
  return records.filter(test).map((r) => r[key]);
}
