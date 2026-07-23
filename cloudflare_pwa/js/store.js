// Shared reactive data store. Loads the bundled data-driven assets once and
// exposes them to every workflow component. Uses Vue's reactive() from the
// vendored global build (window.Vue).

const { reactive } = window.Vue;

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url} (${response.status})`);
  return response.json();
}

async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url} (${response.status})`);
  return response.text();
}

export const store = reactive({
  ready: false,
  error: null,
  mappingProfiles: [],
  builderManifest: null,
  webvocProperties: [],
  webvocClasses: [],
  mappingCatalog: [],
  mappingSuggestions: [],
  samples: [],
  theme: localStorage.getItem('theme') || 'auto',
  lang: localStorage.getItem('lang') || 'en',
  // Cross-workflow handoff: the most recent Convert result (for the Passport
  // workflow's "Continue to Product Passport").
  lastConversion: null,
  // Lazily loaded, larger assets.
  individualsByClass: null,
  passportSchema: null,
});

export async function loadStore() {
  try {
    const [mvp, v2, v3, v4, v5, v6, manifest, properties, classes, catalog, suggestions] = await Promise.all([
      fetchJson('data/mappings/mapping_mvp.json'),
      fetchJson('data/mappings/mapping_v0_2.json'),
      fetchJson('data/mappings/mapping_v0_3.json'),
      fetchJson('data/mappings/mapping_v0_4.json'),
      fetchJson('data/mappings/mapping_v0_5.json'),
      fetchJson('data/mappings/mapping_v0_6.json'),
      fetchJson('data/builder_manifest.json'),
      fetchJson('data/webvoc_properties.json'),
      fetchJson('data/webvoc_classes.json'),
      fetchJson('data/mapping_catalog.json'),
      fetchJson('data/mapping_suggestions_v0_1.json'),
    ]);
    store.mappingProfiles = [
      { id: 'v0_6', label: 'Clean standards output (v0.6, current)', config: v6 },
      { id: 'v0_5', label: 'Structured review output (v0.5, archived)', config: v5 },
      { id: 'v0_4', label: 'Review-safe WebVoc (v0.4, archived)', config: v4 },
      { id: 'v0_3', label: 'Certifications & Documents (v0.3, archived)', config: v3 },
      { id: 'v0_2', label: 'Food (v0.2, archived)', config: v2 },
      { id: 'mvp', label: 'MVP identity (v0.1, archived)', config: mvp },
    ];
    store.builderManifest = manifest;
    store.webvocProperties = properties;
    store.webvocClasses = classes;
    store.mappingCatalog = catalog;
    store.mappingSuggestions = suggestions;
    store.samples = [
      { id: 'example', label: 'example_product.xml — full sample', file: 'data/samples/example_product.xml' },
      { id: 'certified', label: 'certified_product_with_documents.xml', file: 'data/samples/certified_product_with_documents.xml' },
      { id: 'food', label: 'food_product_full.xml', file: 'data/samples/food_product_full.xml' },
      { id: 'minimal', label: 'minimal_product.xml', file: 'data/samples/minimal_product.xml' },
      { id: 'partial', label: 'partially_mapped_product.xml', file: 'data/samples/partially_mapped_product.xml' },
    ];
    store.ready = true;
  } catch (err) {
    store.error = err.message;
  }
}

export function loadSampleText(file) {
  return fetchText(file);
}

// Governed term ids the app itself emits (mapping profiles + builder manifest),
// so the JSON-LD term check never flags the app's own valid output.
export function governedTerms() {
  const terms = [];
  for (const profile of store.mappingProfiles) {
    const config = profile.config;
    for (const field of config.fields || []) terms.push(field.jsonld_property);
    for (const om of config.object_mappings || []) {
      terms.push(om.jsonld_property, om.object_type);
      for (const field of om.fields || []) terms.push(field.jsonld_property);
    }
  }
  const manifest = store.builderManifest;
  if (manifest) {
    for (const group of manifest.groups || []) {
      for (const field of group.properties || []) {
        terms.push(field.property_id);
        for (const sub of field.object_fields || []) terms.push(sub.property_id);
      }
    }
  }
  return terms.filter(Boolean);
}

// Lazy loaders for the larger assets (kept off the first-paint critical path).
export async function loadIndividuals() {
  if (!store.individualsByClass) {
    store.individualsByClass = await fetchJson('data/webvoc_individuals.json');
  }
  return store.individualsByClass;
}

export async function loadPassportSchema() {
  if (!store.passportSchema) {
    store.passportSchema = await fetchJson('data/dpp_minimal.schema.json');
  }
  return store.passportSchema;
}

export function setLang(lang) {
  store.lang = lang;
  localStorage.setItem('lang', lang);
}

export function applyTheme(theme) {
  store.theme = theme;
  localStorage.setItem('theme', theme);
  const root = document.documentElement;
  if (theme === 'auto') {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', theme);
  }
}
