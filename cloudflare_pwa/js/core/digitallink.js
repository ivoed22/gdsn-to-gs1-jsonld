// Port of src/gdsn_to_gs1_jsonld/digital_link.py. Constructs the GS1 Digital
// Link URI *form* for a GTIN and renders it as a QR SVG entirely offline via
// the vendored qrcode-generator library (window.qrcode). It never checks,
// claims, or implies that the link is registered, resolvable, or live.

export const DIGITAL_LINK_BASE = 'https://id.gs1.org';

// Reused verbatim wherever the URI is presented, so the no-resolution caveat
// cannot drift between surfaces.
export const DIGITAL_LINK_CAVEAT =
  'GS1 Digital Link URI form constructed offline from the GTIN. This does ' +
  'not check or claim that the link is registered, resolvable, or live.';

export class DigitalLinkError extends Error {}

// digital_link.build_digital_link_uri — digits-only guard (full check-digit
// validation remains the converter/validator's job).
export function buildDigitalLinkUri(gtin) {
  const cleaned = String(gtin == null ? '' : gtin).trim();
  if (!cleaned || !/^\d+$/.test(cleaned)) {
    throw new DigitalLinkError(
      `GTIN must be a non-empty digit string, got ${JSON.stringify(gtin)}.`
    );
  }
  return `${DIGITAL_LINK_BASE}/01/${cleaned}`;
}

// digital_link.digital_link_qr_svg — deterministic QR SVG for a URI.
export function digitalLinkQrSvg(uri) {
  const qrcode = globalThis.qrcode;
  if (typeof qrcode !== 'function') {
    throw new DigitalLinkError(
      'The QR generator is unavailable (vendor/qrcode.min.js failed to load).'
    );
  }
  // typeNumber 0 = auto-fit to the data; error-correction level 'M'.
  const qr = qrcode(0, 'M');
  qr.addData(uri);
  qr.make();
  // cellSize 4px, quiet-zone margin of 4 cells.
  return qr.createSvgTag({ cellSize: 4, margin: 4, scalable: true });
}
