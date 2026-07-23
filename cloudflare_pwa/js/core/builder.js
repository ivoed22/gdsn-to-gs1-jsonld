// Port of the manual-builder functions in src/gdsn_to_gs1_jsonld/jsonld_builder.py
// (infer_input_type, update/validate/serialize builder state, nested objects).
// Pure logic — no DOM — so it runs in the browser and under Node tests.

import { GS1_WEBVOC_CONTEXT, SCHEMA_ORG_CONTEXT, jsonldString } from './jsonld.js';

export const PROTOTYPE_GOVERNANCE_WARNING =
  'Manual JSON-LD prototype. This output is entered manually, not generated ' +
  'from GDSN XML. It is not BMS/XPath traceable unless linked to governed ' +
  'mapping evidence. It is not an official GS1 validation result.';

// ---- metadata helpers ------------------------------------------------------

function compactPropertyName(propertyId) {
  return propertyId.includes(':') ? propertyId.split(':').slice(1).join(':') : propertyId;
}

function metadataRange(metadata) {
  const value = metadata.range;
  if (Array.isArray(value)) return value.map(String);
  if (value) return [String(value)];
  return [];
}

function isQuantityProperty(propertyId, ranges) {
  const compact = compactPropertyName(propertyId).toLowerCase();
  const tokens = ['content', 'weight', 'height', 'width', 'depth', 'dimension'];
  return (
    ranges.includes('gs1:QuantitativeValue') ||
    tokens.some((token) => compact.includes(token))
  );
}

// jsonld_builder.infer_input_type.
export function inferInputType(propertyMetadata, manifestOverride) {
  if (manifestOverride) return manifestOverride;
  const metadata = propertyMetadata || {};
  const termId = String(metadata.term_id || '');
  const ranges = metadataRange(metadata);
  const rangeSet = new Set(ranges);
  if (isQuantityProperty(termId, ranges)) return 'quantity';
  if (rangeSet.has('rdf:langString')) return 'language_text';
  if (rangeSet.has('xsd:boolean')) return 'checkbox';
  if (rangeSet.has('xsd:integer')) return 'integer';
  if (rangeSet.has('xsd:float') || rangeSet.has('xsd:decimal') || rangeSet.has('xsd:double')) {
    return 'number';
  }
  if (rangeSet.has('xsd:dateTime')) return 'datetime';
  if (rangeSet.has('xsd:date')) return 'date';
  if (rangeSet.has('xsd:anyURI')) return 'url';
  if (rangeSet.has('xsd:string') || ranges.length === 0) return 'text';
  return 'unsupported';
}

function metadataForProperty(propertyMetadata, propertyId) {
  const value = propertyMetadata[propertyId];
  return value && typeof value === 'object' ? value : {};
}

// Port of prototype._full_codelist_options: every WebVoc-defined individual
// across a property's range classes, de-duplicated by value and sorted by label.
export function fullCodelistOptions(rangeClasses, individualsByClass) {
  const seen = new Set();
  const options = [];
  for (const rangeClass of rangeClasses || []) {
    for (const option of (individualsByClass && individualsByClass[rangeClass]) || []) {
      if (!seen.has(option.value)) {
        seen.add(option.value);
        options.push(option);
      }
    }
  }
  return options
    .slice()
    .sort((a, b) => {
      const la = a.label.toLowerCase();
      const lb = b.label.toLowerCase();
      return la < lb ? -1 : la > lb ? 1 : 0;
    });
}

// ---- state manipulation ----------------------------------------------------

function entryValue(entry) {
  if (entry && typeof entry === 'object') return entry.value;
  return entry;
}
function entryLanguage(entry) {
  if (entry && typeof entry === 'object') return String(entry.language || '');
  return '';
}
function entryUnitCode(entry) {
  if (entry && typeof entry === 'object') return String(entry.unitCode || '');
  return '';
}

function emptyManualValue(value) {
  if (value == null || value === '') return true;
  if (Array.isArray(value) && value.length === 0) return true;
  if (typeof value === 'string' && !value.trim()) return true;
  return false;
}

function coerceScalar(value, inputType) {
  if (inputType === 'checkbox') return Boolean(value);
  if (inputType === 'integer') {
    const n = Number(value);
    if (!Number.isInteger(n)) throw new Error('not an integer');
    return n;
  }
  if (inputType === 'number' || inputType === 'quantity') {
    const n = Number(value);
    if (!Number.isFinite(n)) throw new Error('not a number');
    return n;
  }
  return value;
}

function looksLikeUrl(value) {
  const match = /^([a-zA-Z][a-zA-Z0-9+.-]*):\/\/([^/?#]*)/.exec(String(value));
  if (!match) return false;
  const scheme = match[1].toLowerCase();
  return (scheme === 'http' || scheme === 'https') && match[2].length > 0;
}

function validGtin(value) {
  const digits = String(value || '').replace(/\D/g, '');
  if (![8, 12, 13, 14].includes(digits.length)) return false;
  const checkDigit = parseInt(digits[digits.length - 1], 10);
  const body = digits.slice(0, -1).split('').reverse();
  let total = 0;
  body.forEach((digit, index) => {
    const multiplier = (index + 1) % 2 === 1 ? 3 : 1;
    total += parseInt(digit, 10) * multiplier;
  });
  return (10 - (total % 10)) % 10 === checkDigit;
}

// jsonld_builder.object_subfield_key.
export function objectSubfieldKey(objectId, subPropertyId) {
  return `${objectId}#${subPropertyId}`;
}

// jsonld_builder.build_empty_builder_state.
export function buildEmptyBuilderState(rootClass = 'Product') {
  return {
    root_class: rootClass,
    product_category: 'General Product',
    default_language: 'en',
    selected_groups: ['core_product_information'],
    values: {},
    validation_warnings: [],
  };
}

// jsonld_builder.update_builder_value.
export function updateBuilderValue(state, propertyId, value, language, unitCode) {
  const updated = {
    ...state,
    values: { ...(state.values || {}) },
    validation_warnings: [...(state.validation_warnings || [])],
  };
  if (emptyManualValue(value) && !language && !unitCode) {
    delete updated.values[propertyId];
    return updated;
  }
  let entry;
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    entry = { ...value };
  } else {
    entry = { value };
  }
  if (language) entry.language = language;
  if (unitCode) entry.unitCode = unitCode;
  updated.values[propertyId] = entry;
  return updated;
}

// ---- manifest navigation ---------------------------------------------------

// jsonld_builder.get_builder_groups.
export function getBuilderGroups(manifest, category) {
  const categories = {};
  for (const item of manifest.product_categories || []) {
    if (item && typeof item === 'object') categories[item.label] = item;
  }
  const enabled = (categories[category] || {}).groups;
  const enabledKeys = new Set(enabled || []);
  const groups = (manifest.groups || []).filter((g) => g && typeof g === 'object');
  if (enabledKeys.size === 0) return groups;
  return groups.filter((group) => enabledKeys.has(group.key));
}

// jsonld_builder.get_builder_fields.
export function getBuilderFields(manifest, group) {
  const groupKey = group && typeof group === 'object' ? group.key : group;
  for (const item of manifest.groups || []) {
    if (item && typeof item === 'object' && item.key === groupKey) {
      return (item.properties || []).filter((f) => f && typeof f === 'object');
    }
  }
  return [];
}

// Build the property-metadata index (prototype._property_metadata_index):
// WebVoc property facts (range/label/comment) overlaid with per-field manifest
// configuration, keyed by term_id.
export function buildPropertyMetadataIndex(manifest, webvocProperties) {
  const index = {};
  for (const property of webvocProperties || []) {
    index[property.term_id] = {
      term_id: property.term_id,
      label: property.label,
      comment: property.comment,
      domain: [...(property.domain || [])],
      range: [...(property.range || [])],
      sub_property_of: [...(property.sub_property_of || [])],
      type: [...(property.type || [])],
      term_status: property.term_status,
      is_link_type: property.is_link_type,
      supported_in_v0_10: true,
    };
  }
  for (const group of manifest.groups || []) {
    for (const field of group.properties || []) {
      const propertyId = field.property_id;
      if (!propertyId) continue;
      const metadata = { ...(index[propertyId] || { term_id: propertyId }) };
      metadata.requirement = field.requirement || 'optional';
      metadata.input_type_override = field.input_type_override ?? null;
      metadata.example_value = field.example_value || '';
      metadata.help_text = field.help_text || '';
      metadata.appears_because = field.appears_because || '';
      metadata.supported_in_v0_10 = field.supported_in_v0_10 ?? true;
      metadata.planned_reason = field.planned_reason || '';
      metadata.object_type = field.object_type ?? null;
      metadata.object_fields = field.object_fields ?? null;
      metadata.options = field.options ?? null;
      index[propertyId] = metadata;
    }
  }
  return index;
}

// ---- validation (jsonld_builder.validate_builder_state) --------------------

export function validateBuilderState(state, propertyMetadata) {
  const warnings = [PROTOTYPE_GOVERNANCE_WARNING];
  const values = state.values || {};
  const gtin = String(entryValue(values['gs1:gtin']) || '').trim();
  if (!gtin) {
    warnings.push(
      'Missing GTIN. The generated JSON-LD will not include a GS1 Digital Link-style @id.'
    );
  } else if (!validGtin(gtin)) {
    warnings.push('Invalid GTIN format or check digit.');
  }

  for (const [propertyId, entry] of Object.entries(values)) {
    if (propertyId.includes('#')) continue;
    const metadata = metadataForProperty(propertyMetadata, propertyId);
    const inputType = inferInputType(
      metadata,
      metadata.input_type_override || metadata.input_type
    );
    const supported = metadata.supported_in_v0_10 ?? true;
    const value = entryValue(entry);
    const unitCode = entryUnitCode(entry);
    if (
      emptyManualValue(value) &&
      inputType !== 'checkbox' &&
      !(inputType === 'quantity' && unitCode)
    ) {
      continue;
    }
    if (!supported) {
      warnings.push(`${propertyId} is not supported in v0.10 and will not be emitted.`);
    }
    if (inputType === 'unsupported') {
      const ranges = metadataRange(metadata).join(', ') || 'unknown range';
      warnings.push(
        `${propertyId} has unsupported nested or complex range (${ranges}) and will not be emitted.`
      );
    }
    if (inputType === 'url' && value && !looksLikeUrl(String(value))) {
      warnings.push(`${propertyId} is not a valid HTTP(S) URL.`);
    }
    if (inputType === 'language_text' && value && !entryLanguage(entry)) {
      warnings.push(`${propertyId} needs a language tag.`);
    }
    if (
      (inputType === 'integer' || inputType === 'number' || inputType === 'quantity') &&
      value != null &&
      value !== ''
    ) {
      try {
        coerceScalar(value, inputType);
      } catch (err) {
        warnings.push(`${propertyId} must be a valid number.`);
      }
    }
    if (inputType === 'quantity') {
      if (value != null && value !== '' && !unitCode) {
        warnings.push(`${propertyId} has a quantity value without unitCode.`);
      }
      if (unitCode && (value == null || value === '')) {
        warnings.push(`${propertyId} has unitCode without a quantity value.`);
      }
    }
  }

  for (const [objectId, meta] of Object.entries(propertyMetadata)) {
    if (!meta || typeof meta !== 'object') continue;
    if ((meta.input_type_override || meta.input_type) !== 'object') continue;
    for (const sub of meta.object_fields || []) {
      const subId = sub.property_id;
      if (!subId) continue;
      const subEntry = values[objectSubfieldKey(objectId, subId)];
      if (subEntry == null) continue;
      const subType = sub.input_type_override || sub.input_type || 'text';
      const subValue = entryValue(subEntry);
      if (emptyManualValue(subValue)) continue;
      if (subType === 'url' && !looksLikeUrl(String(subValue))) {
        warnings.push(`${objectId} / ${subId} is not a valid HTTP(S) URL.`);
      }
      if (subType === 'language_text' && !entryLanguage(subEntry)) {
        warnings.push(`${objectId} / ${subId} needs a language tag.`);
      }
    }
  }

  return [...new Set(warnings)];
}

// ---- serialization (jsonld_builder.serialize_builder_state_to_jsonld) ------

function emitScalarLike(entry, inputType) {
  const value = entryValue(entry);
  if (emptyManualValue(value) && value !== false) return null;
  if (inputType === 'language_text') {
    const language = entryLanguage(entry);
    if (!language) return null;
    return [{ '@language': language, '@value': String(value) }];
  }
  if (inputType === 'quantity') {
    const unitCode = entryUnitCode(entry);
    if (value == null || value === '' || !unitCode) return null;
    try {
      return { value: coerceScalar(value, 'quantity'), unitCode };
    } catch (err) {
      return null;
    }
  }
  if (inputType === 'url') {
    return looksLikeUrl(String(value)) ? String(value) : null;
  }
  if (inputType === 'code') {
    return { '@id': String(value) };
  }
  try {
    return coerceScalar(value, inputType);
  } catch (err) {
    return null;
  }
}

function serializeObjectField(objectId, metadata, values) {
  const obj = {};
  const objectType = metadata.object_type;
  if (objectType) obj['@type'] = objectType;
  for (const sub of metadata.object_fields || []) {
    const subId = sub.property_id;
    if (!subId) continue;
    const entry = values[objectSubfieldKey(objectId, subId)];
    if (entry == null) continue;
    const subType = sub.input_type_override || sub.input_type || 'text';
    const emitted = emitScalarLike(entry, subType);
    if (emitted == null || emitted === '' || (Array.isArray(emitted) && emitted.length === 0)) {
      continue;
    }
    obj[compactPropertyName(subId)] = emitted;
  }
  if (Object.keys(obj).length <= (objectType ? 1 : 0)) return null;
  return obj;
}

export function serializeBuilderStateToJsonld(state, propertyMetadata) {
  const data = {
    '@context': [GS1_WEBVOC_CONTEXT, SCHEMA_ORG_CONTEXT],
    '@type': state.root_class || 'Product',
  };
  const values = state.values || {};
  const gtin = String(entryValue(values['gs1:gtin']) || '').trim();
  if (gtin) data['@id'] = `https://id.gs1.org/01/${gtin}`;

  for (const propertyId of Object.keys(values).sort()) {
    if (propertyId.includes('#')) continue;
    const entry = values[propertyId];
    const value = entryValue(entry);
    if (emptyManualValue(value) && value !== false) continue;
    const metadata = metadataForProperty(propertyMetadata, propertyId);
    const inputType = inferInputType(
      metadata,
      metadata.input_type_override || metadata.input_type
    );
    if (!(metadata.supported_in_v0_10 ?? true) || inputType === 'unsupported') continue;
    if (inputType === 'object') continue;
    const compactName = compactPropertyName(propertyId);
    if (inputType === 'language_text') {
      const language = entryLanguage(entry);
      if (!language) continue;
      data[compactName] = [{ '@language': language, '@value': String(value) }];
    } else if (inputType === 'quantity') {
      const unitCode = entryUnitCode(entry);
      if (value == null || value === '' || !unitCode) continue;
      let quantityValue;
      try {
        quantityValue = coerceScalar(value, 'quantity');
      } catch (err) {
        continue;
      }
      data[compactName] = { value: quantityValue, unitCode };
    } else if (inputType === 'url') {
      if (looksLikeUrl(String(value))) data[compactName] = String(value);
    } else if (inputType === 'code') {
      data[compactName] = { '@id': String(value) };
    } else {
      try {
        data[compactName] = coerceScalar(value, inputType);
      } catch (err) {
        continue;
      }
    }
  }

  for (const objectId of Object.keys(propertyMetadata).sort()) {
    const meta = propertyMetadata[objectId];
    if (!meta || typeof meta !== 'object') continue;
    if ((meta.input_type_override || meta.input_type) !== 'object') continue;
    if (!(meta.supported_in_v0_10 ?? true)) continue;
    const obj = serializeObjectField(objectId, meta, values);
    if (obj) data[compactPropertyName(objectId)] = obj;
  }

  return data;
}

export { jsonldString, inferInputType as _inferInputType };
