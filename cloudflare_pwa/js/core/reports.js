// Download artifacts for the Convert workflow: JSON-LD, mapping report (CSV),
// validation JSON, unmapped JSON, and a self-contained printable HTML product
// report (port of report.py). Browser-only (Blob downloads + QR SVG).

import { jsonldString } from './jsonld.js';
import { buildXlsx } from './xlsx.js';
import { assessReadiness, SCOPE_NOTE } from './readiness.js';
import {
  DIGITAL_LINK_CAVEAT,
  DigitalLinkError,
  buildDigitalLinkUri,
  digitalLinkQrSvg,
} from './digitallink.js';

// reporter.json_bytes — indent 2, non-ASCII preserved, no trailing newline.
export function jsonString(data) {
  return JSON.stringify(data, null, 2);
}

export { jsonldString };

// ---- JSON-LD extraction helpers (product_passport_builder.extract_*) -------

export function extractGtin(jsonldData) {
  const direct = jsonldData['gs1:gtin'];
  if (direct) return String(direct);
  const id = jsonldData['@id'];
  if (typeof id === 'string') {
    const match = /\/01\/(\d+)/.exec(id);
    if (match) return match[1];
  }
  return null;
}

export function extractProductName(jsonldData) {
  const name = jsonldData['gs1:productName'];
  if (Array.isArray(name) && name.length) {
    const first = name[0];
    if (first && typeof first === 'object' && '@value' in first) return first['@value'];
  }
  if (typeof name === 'string') return name;
  return null;
}

// ---- mapping report CSV ----------------------------------------------------

function csvCell(value) {
  let cell;
  if (value == null) cell = '';
  else if (typeof value === 'object') cell = JSON.stringify(value);
  else cell = String(value);
  if (/[",\n\r]/.test(cell)) {
    cell = `"${cell.replace(/"/g, '""')}"`;
  }
  return cell;
}

const MAPPING_COLUMNS = [
  'id',
  'description',
  'xpath',
  'canonical_field',
  'jsonld_property',
  'required',
  'found',
  'value',
  'status',
  'message',
];

// CSV of the mapping-report rows (same data the Python xlsx report carried).
export function mappingReportCsv(rows) {
  const lines = [MAPPING_COLUMNS.map(csvCell).join(',')];
  for (const row of rows) {
    lines.push(MAPPING_COLUMNS.map((column) => csvCell(row[column])).join(','));
  }
  return `${lines.join('\r\n')}\r\n`;
}

// Real .xlsx of the mapping-report rows (matches the Streamlit output format).
export function mappingReportXlsx(rows) {
  const body = rows.map((row) =>
    MAPPING_COLUMNS.map((column) => {
      const value = row[column];
      if (value == null) return '';
      return typeof value === 'object' ? JSON.stringify(value) : value;
    })
  );
  return buildXlsx('Mapping report', [MAPPING_COLUMNS, ...body]);
}

// ---- self-contained HTML product report (report.py) ------------------------

const TOKENS = {
  surface_default: '#ffffff',
  surface_muted: '#f5f7fb',
  border_default: '#dbe3ee',
  text_primary: '#152238',
  text_secondary: '#53647a',
  accent_primary: '#1769aa',
  state_success: '#16794b',
  state_warning: '#9a6700',
  state_error: '#b42318',
};

const LEVEL_COLORS = {
  structurally_ready: TOKENS.state_success,
  attention_points: TOKENS.state_warning,
  review_required: TOKENS.state_error,
};

const GOVERNANCE_FOOTER =
  'Prototype/reference output. Not official GS1 validation. No production ' +
  'compliance claim. Not an EU DPP conformity assessment.';

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function reportCss() {
  return `
  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: ${TOKENS.text_primary}; background: ${TOKENS.surface_default};
    margin: 2rem auto; max-width: 60rem; line-height: 1.5; }
  h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
  h2 { font-size: 1.1rem; border-bottom: 1px solid ${TOKENS.border_default};
    padding-bottom: 0.25rem; margin-top: 2rem; }
  .eyebrow { color: ${TOKENS.accent_primary}; text-transform: uppercase;
    letter-spacing: 0.08em; font-size: 0.75rem; font-weight: 600; }
  .muted { color: ${TOKENS.text_secondary}; font-size: 0.9rem; }
  .level-badge { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px;
    color: ${TOKENS.surface_default}; font-weight: 600; font-size: 0.9rem; }
  table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border: 1px solid ${TOKENS.border_default};
    font-size: 0.9rem; vertical-align: top; }
  th { background: ${TOKENS.surface_muted}; }
  pre { background: ${TOKENS.surface_muted}; border: 1px solid ${TOKENS.border_default};
    padding: 1rem; overflow-x: auto; font-size: 0.8rem; }
  footer { margin-top: 2.5rem; padding-top: 1rem; border-top: 2px solid ${TOKENS.border_default};
    color: ${TOKENS.text_secondary}; font-size: 0.85rem; }
  @media print { body { margin: 0.5rem; } pre { white-space: pre-wrap; } }
  `;
}

function dimensionRowsHtml(dimensions) {
  const labels = {
    structural_validation: 'Structural validation',
    mapping_coverage: 'Mapping coverage',
    codelist_conformance: 'Codelist conformance',
    dpp_relevance: 'DPP relevance',
  };
  return Object.entries(labels)
    .map(([key, label]) => {
      const dimension = dimensions[key];
      return (
        '<tr>' +
        `<th scope='row'>${escapeHtml(label)}</th>` +
        `<td><code>${escapeHtml(String(dimension.status))}</code></td>` +
        `<td>${escapeHtml(String(dimension.detail))}</td>` +
        '</tr>'
      );
    })
    .join('');
}

export function buildProductReportHtml({
  jsonld_data: jsonldData,
  validation_report: validationReport,
  mapping_report_rows: mappingReportRows,
  unmapped_fields: unmappedFields,
  generated_note: generatedNote = null,
}) {
  const assessment = assessReadiness({
    validation_report: validationReport,
    mapping_report_rows: mappingReportRows,
    unmapped_fields: unmappedFields,
  });
  const level = assessment.readiness_level;
  const dimensions = assessment.dimensions;
  const coverage = dimensions.mapping_coverage;

  const gtin = extractGtin(jsonldData) || 'unknown';
  const productName = extractProductName(jsonldData) || '—';
  const productId = String(jsonldData['@id'] || '—');

  let digitalLinkSection = '';
  try {
    const uri = buildDigitalLinkUri(gtin);
    digitalLinkSection = `
<h2>GS1 Digital Link</h2>
<p><code>${escapeHtml(uri)}</code></p>
<div style="max-width: 10rem;">${digitalLinkQrSvg(uri)}</div>
<p class="muted">${escapeHtml(DIGITAL_LINK_CAVEAT)}</p>
`;
  } catch (err) {
    if (!(err instanceof DigitalLinkError)) throw err;
    digitalLinkSection = '';
  }

  const formattedJsonld = JSON.stringify(jsonldData, null, 2);
  const generatedHtml = generatedNote
    ? `<p class='muted'>${escapeHtml(generatedNote)}</p>`
    : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Product report — GTIN ${escapeHtml(gtin)}</title>
<style>${reportCss()}</style>
</head>
<body>
<header>
  <p class="eyebrow">GDSN to GS1 JSON-LD — product report</p>
  <h1>${escapeHtml(productName)}</h1>
  <p class="muted">GTIN ${escapeHtml(gtin)} · <code>${escapeHtml(productId)}</code></p>
  ${generatedHtml}
</header>

<h2>DPP readiness — traceability &amp; structural signals</h2>
<p>
  Overall level:
  <span class="level-badge" style="background:${LEVEL_COLORS[level] || TOKENS.text_secondary}">
    ${escapeHtml(level.replace(/_/g, ' '))}
  </span>
</p>
<table>
  <thead><tr><th>Dimension</th><th>Status</th><th>Detail</th></tr></thead>
  <tbody>${dimensionRowsHtml(dimensions)}</tbody>
</table>
<p class="muted">${escapeHtml(assessment.scope_note)}</p>

${digitalLinkSection}
<h2>Mapping evidence summary</h2>
<table>
  <tbody>
    <tr><th scope="row">Profile rows found in source</th>
        <td>${coverage.mapped_count}/${coverage.profile_row_count}</td></tr>
    <tr><th scope="row">Populated source elements outside the profile</th>
        <td>${coverage.unmapped_source_element_count}</td></tr>
    <tr><th scope="row">Structural validation</th>
        <td>${validationReport.valid ? 'valid' : 'errors present'} ·
        ${(validationReport.errors || []).length} error(s),
        ${(validationReport.warnings || []).length} warning(s)</td></tr>
  </tbody>
</table>

<h2>Generated GS1 Web Vocabulary JSON-LD</h2>
<pre>${escapeHtml(formattedJsonld)}</pre>

<footer>
  <p>${escapeHtml(SCOPE_NOTE)}</p>
  <p>${escapeHtml(GOVERNANCE_FOOTER)}</p>
</footer>
</body>
</html>
`;
}

// ---- browser download helper ----------------------------------------------

export function downloadText(filename, text, mime = 'text/plain') {
  downloadBlob(filename, new Blob([text], { type: `${mime};charset=utf-8` }));
}

// Download binary data (Uint8Array), e.g. an .xlsx or .zip.
export function downloadBytes(filename, bytes, mime = 'application/octet-stream') {
  downloadBlob(filename, new Blob([bytes], { type: mime }));
}

function downloadBlob(filename, blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
