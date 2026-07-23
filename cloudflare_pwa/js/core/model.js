// Canonical model value types + small structural helpers shared between the
// mapping engine and the JSON-LD builder (kept separate to avoid an import
// cycle). Mirrors canonical_model.py's LanguageValue plus the nested-path
// helpers used by converter.py / jsonld_builder.py.

import { DecimalValue } from './transforms.js';

export class LanguageValue {
  constructor(value, language) {
    this.value = value;
    this.language = language;
  }
  // Mirror pydantic model_dump() field order: value, then language.
  dump() {
    return { value: this.value, language: this.language };
  }
}

// converter._set_nested_value / jsonld_builder._set_nested_value.
export function setNestedValue(target, path, value) {
  const parts = path.split('.');
  let current = target;
  for (let i = 0; i < parts.length - 1; i += 1) {
    const part = parts[i];
    if (current[part] == null || typeof current[part] !== 'object') {
      current[part] = {};
    }
    current = current[part];
  }
  current[parts[parts.length - 1]] = value;
}

// jsonld_builder._get_nested_value.
export function getNestedValue(value, path) {
  let current = value;
  for (const part of path.split('.')) {
    if (current == null) return null;
    if (typeof current === 'object') {
      current = current[part];
    } else {
      return null;
    }
    if (current === undefined) return null;
  }
  return current;
}

// Deep-serialize canonical values into plain JSON-friendly structures:
// DecimalValue -> number, LanguageValue -> {value, language}, recursing into
// arrays/objects. Used for the human-facing mapping-report display values.
export function serializeDeep(value) {
  if (value instanceof DecimalValue) return value.number;
  if (value instanceof LanguageValue) return value.dump();
  if (Array.isArray(value)) return value.map(serializeDeep);
  if (value && typeof value === 'object') {
    const out = {};
    for (const [key, val] of Object.entries(value)) {
      out[key] = serializeDeep(val);
    }
    return out;
  }
  return value;
}
