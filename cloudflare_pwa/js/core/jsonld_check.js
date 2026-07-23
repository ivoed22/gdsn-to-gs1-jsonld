// Structural + WebVoc term check (offline, lightweight — NOT SHACL/RDF).
// Walks a JSON-LD object and flags any property key or @type that does not
// resolve to a term in the bundled GS1 Web Vocabulary 1.17 snapshot. schema.org
// terms are reported as "external, not checked" (no offline schema.org snapshot).
// Honesty: this is a structural term check, not official GS1 validation.

// JSON-LD keywords and structural members that are never vocabulary terms.
const KEYWORDS = new Set(['@context', '@id', '@type', '@value', '@language', '@graph', '@list', '@set']);
const STRUCTURAL_MEMBERS = new Set(['value', 'unitCode']);

function localName(term) {
  return term.includes(':') ? term.split(':').slice(1).join(':') : term;
}

// Build the "known term" sets. `extraKnown` is a list of additional term ids
// the app itself governs (the bundled mapping profiles' jsonld_property values +
// the builder manifest property ids) — these resolve as known even when they
// are not in the curated 1.17 property snapshot, so the check never flags the
// app's own valid output while still catching foreign/typo terms in pasted JSON.
export function buildTermSets(properties, classes, extraKnown = []) {
  const propertyFull = new Set();
  const propertyLocals = new Set();
  const classFull = new Set();
  const classLocals = new Set();
  const extraFull = new Set();
  const extraLocals = new Set();
  for (const p of properties || []) {
    if (!p.term_id) continue;
    propertyFull.add(p.term_id);
    propertyLocals.add(localName(p.term_id));
  }
  for (const c of classes || []) {
    if (!c.term_id) continue;
    classFull.add(c.term_id);
    classLocals.add(localName(c.term_id));
  }
  for (const term of extraKnown) {
    if (typeof term !== 'string' || !term) continue;
    // Strip any dotted nested-property suffix (e.g. gs1:quantityContained.value).
    const base = term.split('.')[0];
    extraFull.add(base);
    extraLocals.add(localName(base));
  }
  return { propertyFull, propertyLocals, classFull, classLocals, extraFull, extraLocals };
}

function isKnownProperty(key, sets) {
  if (sets.propertyFull.has(key) || sets.extraFull.has(key)) return true;
  const local = localName(key);
  return sets.propertyLocals.has(local) || sets.extraLocals.has(local);
}

function isKnownClass(type, sets) {
  if (sets.classFull.has(type) || sets.extraFull.has(type)) return true;
  const local = localName(type);
  return sets.classLocals.has(local) || sets.extraLocals.has(local);
}

export function checkJsonld(jsonld, sets) {
  const issues = [];
  const external = new Set();
  let checkedProps = 0;
  let checkedTypes = 0;

  const visit = (node, path) => {
    if (Array.isArray(node)) {
      node.forEach((item, i) => visit(item, `${path}[${i}]`));
      return;
    }
    if (!node || typeof node !== 'object') return;

    // @type values
    for (const typeValue of [].concat(node['@type'] ?? [])) {
      if (typeof typeValue !== 'string') continue;
      checkedTypes += 1;
      if (typeValue.startsWith('schema:')) {
        external.add(typeValue);
      } else if (!isKnownClass(typeValue, sets)) {
        issues.push({ path: `${path}/@type`, term: typeValue, kind: 'unknown-type' });
      }
    }

    for (const [key, value] of Object.entries(node)) {
      // Never treat @context contents as vocabulary terms, and don't recurse
      // into it (its prefix keys like "schema" are not properties).
      if (key === '@context') continue;
      if (KEYWORDS.has(key)) {
        if (key === '@graph' && value && typeof value === 'object') {
          visit(value, `${path}/${key}`);
        }
        continue;
      }
      if (STRUCTURAL_MEMBERS.has(key)) continue;
      // Vocabulary property position.
      checkedProps += 1;
      if (key.startsWith('schema:')) {
        external.add(key);
      } else if (!isKnownProperty(key, sets)) {
        issues.push({ path: `${path}/${key}`, term: key, kind: 'unknown-property' });
      }
      if (value && typeof value === 'object') visit(value, `${path}/${key}`);
    }
  };

  visit(jsonld, '');
  return {
    ok: issues.length === 0,
    checked_properties: checkedProps,
    checked_types: checkedTypes,
    issues,
    external: [...external].sort(),
    note:
      'Structural term check against the bundled GS1 Web Vocabulary 1.17 ' +
      'snapshot. schema.org terms are external and not checked. This is not ' +
      'official GS1 validation.',
  };
}
