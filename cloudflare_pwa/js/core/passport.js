// Port of src/gdsn_to_gs1_jsonld/product_passport_builder.py (minimal-schema
// prototype mode) + a small draft-07-subset validator for the bundled
// dpp_minimal.schema.json. Prototype/reference only — structural validation
// only, not official GS1 validation, not EU DPP compliance.

import { GS1_WEBVOC_CONTEXT } from './jsonld.js';

export const BUILDER_VERSION = 'v0.13.0';
export const VALIDATION_MODE = 'minimal-schema-prototype';
export const PASSPORT_TYPE_DEFAULT = 'product-passport-prototype';
export const PASSPORT_VERSION_DEFAULT = 'v0.13.0-prototype';
export const STATUS_DEFAULT = 'prototype';

export const PROTOTYPE_NOTICE =
  'Prototype/reference Product Passport JSON-LD generated for standards ' +
  'discussion only. Structural schema validation only. Not official GS1 ' +
  'validation, not EU DPP regulatory compliance, and not production-ready.';

// ---- extraction helpers (tolerant of converter + manual-builder shapes) ----

function asList(value) {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

export function extractLanguageValues(value) {
  const out = [];
  for (const item of asList(value)) {
    if (item && typeof item === 'object') {
      const val = item['@value'] ?? item.value;
      const lang = item['@language'] ?? item.language;
      if (val != null && String(val).trim()) {
        const entry = { '@value': String(val) };
        if (lang) entry['@language'] = String(lang);
        out.push(entry);
      }
    } else if (typeof item === 'string' && item.trim()) {
      out.push({ '@value': item });
    }
  }
  return out;
}

function firstValue(jsonld, keys) {
  for (const key of keys) {
    if (key in jsonld) {
      const values = extractLanguageValues(jsonld[key]);
      if (values.length) return values[0]['@value'];
    }
  }
  return null;
}

export function extractProductIdentifier(jsonld) {
  const identifier = jsonld['@id'] ?? jsonld.id;
  return identifier ? String(identifier) : null;
}

export function extractGtin(jsonld) {
  for (const key of ['gtin', 'gs1:gtin']) {
    const raw = jsonld[key];
    if (typeof raw === 'string' && raw.trim()) return raw.trim();
    if (raw && typeof raw === 'object' && raw['@value']) return String(raw['@value']).trim();
  }
  const identifier = extractProductIdentifier(jsonld);
  if (identifier) {
    const match = /\/01\/(\d{8,14})/.exec(identifier);
    if (match) return match[1];
  }
  return null;
}

export function extractProductName(jsonld) {
  return firstValue(jsonld, ['productName', 'gs1:productName', 'name', 'schema:name']);
}

// ---- envelope builder (build_minimal_product_passport) ---------------------

function defaultPassportId(gtin) {
  return `urn:gdsn-gs1-jsonld:product-passport:${gtin || 'unidentified'}`;
}

function resolveOptions(options) {
  const opts = options || {};
  return {
    passport_id: opts.passport_id || null,
    passport_type: opts.passport_type || PASSPORT_TYPE_DEFAULT,
    passport_version: opts.passport_version || PASSPORT_VERSION_DEFAULT,
    status: opts.status || STATUS_DEFAULT,
    default_language: opts.default_language || 'en',
    include_source_gs1_jsonld: opts.include_source_gs1_jsonld !== false,
    schema_name: 'dpp_minimal.schema.json',
    prototype_notice: opts.prototype_notice || PROTOTYPE_NOTICE,
    generated_at: opts.generated_at || null,
  };
}

export function buildMinimalProductPassport(gs1Jsonld, options) {
  const opts = resolveOptions(options);
  const gtin = extractGtin(gs1Jsonld);
  const productName = extractProductName(gs1Jsonld);
  const passportId = opts.passport_id || defaultPassportId(gtin);
  const identifier =
    extractProductIdentifier(gs1Jsonld) || (gtin ? `https://id.gs1.org/01/${gtin}` : null);

  const envelope = {
    '@context': GS1_WEBVOC_CONTEXT,
    '@type': 'Product',
  };
  if (identifier) envelope['@id'] = identifier;
  envelope.productPassportId = passportId;
  envelope.passportType = opts.passport_type;
  envelope.passportVersion = opts.passport_version;
  envelope.status = opts.status;
  envelope.prototypeNotice = opts.prototype_notice;
  envelope.defaultLanguage = opts.default_language;
  envelope.source = {
    sourceType: 'gs1-web-vocabulary-jsonld',
    sourceFormat: 'json-ld',
    sourceGtin: gtin,
    sourceProductName: productName,
  };
  envelope.validation = {
    validationMode: VALIDATION_MODE,
    schema: opts.schema_name,
    note:
      'Structural validation result is provided separately in the validation ' +
      'report. Passing means only that the JSON matches the selected local ' +
      'structural schema.',
  };
  envelope.createdByVersion = BUILDER_VERSION;
  if (opts.generated_at) envelope.generatedAt = opts.generated_at;
  if (opts.include_source_gs1_jsonld) envelope.product = gs1Jsonld;
  return envelope;
}

// ---- minimal draft-07-subset validator for dpp_minimal.schema.json ---------

function matchesSingle(value, schema) {
  switch (schema.type) {
    case 'string':
      return typeof value === 'string';
    case 'array':
      if (!Array.isArray(value)) return false;
      if (schema.items && schema.items.type) {
        return value.every((item) => matchesSingle(item, schema.items));
      }
      return true;
    case 'object':
      return value != null && typeof value === 'object' && !Array.isArray(value);
    case 'number':
      return typeof value === 'number';
    case 'boolean':
      return typeof value === 'boolean';
    default:
      return true;
  }
}

function matchesSchema(value, propSchema) {
  if (propSchema.oneOf) return propSchema.oneOf.some((s) => matchesSchema(value, s));
  if (propSchema.type) return matchesSingle(value, propSchema);
  return true;
}

// Returns a report mirroring product_passport_sources.validate_product_passport_json.
export function validateProductPassport(instance, schema) {
  const errors = [];
  if (schema.type === 'object' && (instance == null || typeof instance !== 'object' || Array.isArray(instance))) {
    errors.push('Instance must be a JSON object.');
  } else {
    for (const req of schema.required || []) {
      if (!(req in instance)) errors.push(`Missing required property '${req}'.`);
    }
    const props = schema.properties || {};
    for (const [key, value] of Object.entries(instance)) {
      const propSchema = props[key];
      if (!propSchema) continue; // additionalProperties: true
      if (!matchesSchema(value, propSchema)) {
        errors.push(`Property '${key}' does not match the schema type.`);
      }
    }
  }
  return {
    validation_status: errors.length ? 'invalid' : 'valid',
    errors,
    warnings: [],
    validator_mode: 'structural-subset',
    schema_file: schema['$id'] || 'dpp_minimal.schema.json',
    prototype_warning: PROTOTYPE_NOTICE,
  };
}
