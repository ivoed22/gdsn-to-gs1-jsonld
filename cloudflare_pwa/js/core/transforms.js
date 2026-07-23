// Port of src/gdsn_to_gs1_jsonld/utils.py — value transforms + validators.
// Framework-free, environment-agnostic (browser + Node). No DOM dependency.

// A decimal value is represented as a plain JS number tagged so the JSON-LD
// builder can mirror Python's serializable_value (int when integral, else
// float). JSON.stringify already renders integral numbers without a decimal
// point, so a bare number suffices; we keep a marker class only to distinguish
// "this came from to_decimal" from a string during the transform pipeline.
export class DecimalValue {
  constructor(number) {
    this.number = number;
  }
  toString() {
    return String(this.number);
  }
}

export function normalizeWhitespace(value) {
  return value.replace(/\s+/g, ' ').trim();
}

export function isValidUrl(value) {
  // Mirror urllib.parse.urlparse: scheme in {http, https} and a non-empty
  // network location (host).
  const match = /^([a-zA-Z][a-zA-Z0-9+.-]*):\/\/([^/?#]*)/.exec(value);
  if (!match) return false;
  const scheme = match[1].toLowerCase();
  const netloc = match[2];
  return (scheme === 'http' || scheme === 'https') && netloc.length > 0;
}

export function isValidGtin(value) {
  if (![8, 12, 13, 14].includes(value.length) || !/^\d+$/.test(value)) {
    return false;
  }
  const digits = value.split('').map((d) => parseInt(d, 10));
  const body = digits.slice(0, -1).reverse();
  let weightedSum = 0;
  body.forEach((digit, index) => {
    weightedSum += digit * (index % 2 === 0 ? 3 : 1);
  });
  const expected = (10 - (weightedSum % 10)) % 10;
  return digits[digits.length - 1] === expected;
}

// Mirror Python's Decimal(value) acceptance for the data we handle: an
// optional sign, integer/fraction, optional exponent. Rejects anything else.
const DECIMAL_RE = /^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/;

function toDecimal(value) {
  if (!DECIMAL_RE.test(value.trim())) {
    throw new Error(`'${value}' is not a decimal`);
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new Error(`'${value}' is not a decimal`);
  }
  return new DecimalValue(number);
}

function toDate(value) {
  // date.fromisoformat then datetime.fromisoformat(...).date().isoformat().
  const match = /^(\d{4})-(\d{2})-(\d{2})([T ].*)?$/.exec(value);
  if (match) {
    const [, y, m, d] = match;
    const year = Number(y);
    const month = Number(m);
    const day = Number(d);
    const dt = new Date(Date.UTC(year, month - 1, day));
    if (
      dt.getUTCFullYear() === year &&
      dt.getUTCMonth() === month - 1 &&
      dt.getUTCDate() === day
    ) {
      return `${y}-${m}-${d}`;
    }
  }
  throw new Error(`'${value}' is not an ISO date or datetime`);
}

// Apply a single named transform. Throws Error (mirrors Python ValueError)
// on an invalid value so the caller can record a transform/validation error.
export function applyTransform(value, transform) {
  switch (transform) {
    case 'trim':
      return value.trim();
    case 'normalize_whitespace':
      return normalizeWhitespace(value);
    case 'uppercase':
      return value.toUpperCase();
    case 'to_decimal':
      return toDecimal(value);
    case 'to_date':
      return toDate(value);
    case 'validate_gtin':
      if (!isValidGtin(value)) {
        throw new Error(`'${value}' is not a valid GTIN`);
      }
      return value;
    case 'validate_url':
      if (!isValidUrl(value)) {
        throw new Error(`'${value}' is not a valid HTTP(S) URL`);
      }
      return value;
    default:
      throw new Error(`Unknown transform: ${transform}`);
  }
}

// Mirror utils.serializable_value: Decimal -> number (int when integral).
export function serializableValue(value) {
  if (value instanceof DecimalValue) {
    return value.number;
  }
  return value;
}
