"""Self-contained offline HTML product report (v0.32.0 Report Center).

Builds ONE printable HTML document per converted product: identity, the
v0.31.0 readiness assessment, mapping evidence and codelist summaries, and
the generated JSON-LD. Inline CSS only (values from DESIGN.md tokens), no
external resources, no scripts — the file must open identically from an
email attachment or a USB stick, fully offline.

This is an outward-facing artifact, so the no-claims rules matter double
here: the readiness scope note and the standard governance negations are
rendered verbatim in the footer, and no restricted claim phrase appears
without negation. Deterministic: same conversion in, same bytes out (no
timestamp unless the caller explicitly passes one).
"""

from __future__ import annotations

import json
from html import escape
from typing import Any

from .product_passport_builder import extract_gtin, extract_product_name
from .readiness import assess_readiness

# DESIGN.md color tokens (kept literal so the report has no dependency on
# app/ or any stylesheet file).
_TOKENS = {
    "surface_default": "#ffffff",
    "surface_muted": "#f5f7fb",
    "border_default": "#dbe3ee",
    "text_primary": "#152238",
    "text_secondary": "#53647a",
    "accent_primary": "#1769aa",
    "state_success": "#16794b",
    "state_warning": "#9a6700",
    "state_error": "#b42318",
}

_LEVEL_COLORS = {
    "structurally_ready": _TOKENS["state_success"],
    "attention_points": _TOKENS["state_warning"],
    "review_required": _TOKENS["state_error"],
}

_GOVERNANCE_FOOTER = (
    "Prototype/reference output. Not official GS1 validation. No production "
    "compliance claim. Not an EU DPP conformity assessment."
)


def _css() -> str:
    return f"""
    body {{
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      color: {_TOKENS['text_primary']};
      background: {_TOKENS['surface_default']};
      margin: 2rem auto;
      max-width: 60rem;
      line-height: 1.5;
    }}
    h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
    h2 {{
      font-size: 1.1rem;
      border-bottom: 1px solid {_TOKENS['border_default']};
      padding-bottom: 0.25rem;
      margin-top: 2rem;
    }}
    .eyebrow {{
      color: {_TOKENS['accent_primary']};
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .muted {{ color: {_TOKENS['text_secondary']}; font-size: 0.9rem; }}
    .level-badge {{
      display: inline-block;
      padding: 0.2rem 0.7rem;
      border-radius: 999px;
      color: {_TOKENS['surface_default']};
      font-weight: 600;
      font-size: 0.9rem;
    }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 0.5rem; }}
    th, td {{
      text-align: left;
      padding: 0.4rem 0.6rem;
      border: 1px solid {_TOKENS['border_default']};
      font-size: 0.9rem;
      vertical-align: top;
    }}
    th {{ background: {_TOKENS['surface_muted']}; }}
    pre {{
      background: {_TOKENS['surface_muted']};
      border: 1px solid {_TOKENS['border_default']};
      padding: 1rem;
      overflow-x: auto;
      font-size: 0.8rem;
    }}
    footer {{
      margin-top: 2.5rem;
      padding-top: 1rem;
      border-top: 2px solid {_TOKENS['border_default']};
      color: {_TOKENS['text_secondary']};
      font-size: 0.85rem;
    }}
    @media print {{ body {{ margin: 0.5rem; }} pre {{ white-space: pre-wrap; }} }}
    """


def _dimension_rows_html(dimensions: dict[str, dict[str, Any]]) -> str:
    labels = {
        "structural_validation": "Structural validation",
        "mapping_coverage": "Mapping coverage",
        "codelist_conformance": "Codelist conformance",
        "dpp_relevance": "DPP relevance",
    }
    rows = []
    for key, label in labels.items():
        dimension = dimensions[key]
        rows.append(
            "<tr>"
            f"<th scope='row'>{escape(label)}</th>"
            f"<td><code>{escape(str(dimension['status']))}</code></td>"
            f"<td>{escape(str(dimension['detail']))}</td>"
            "</tr>"
        )
    return "".join(rows)


def build_product_report_html(
    *,
    jsonld_data: dict[str, Any],
    validation_report: dict[str, Any],
    mapping_report_rows: list[dict[str, Any]],
    unmapped_fields: dict[str, Any],
    codelist_validation: list[dict[str, Any]] | None = None,
    generated_note: str | None = None,
) -> str:
    """Build the self-contained HTML report for one converted product.

    All inputs are existing ``ConversionResult`` fields. ``generated_note``
    is an optional free-text line (e.g. a date the caller chooses to
    include); omitted by default so identical input produces identical
    bytes.
    """
    assessment = assess_readiness(
        validation_report=validation_report,
        mapping_report_rows=mapping_report_rows,
        unmapped_fields=unmapped_fields,
        codelist_validation=codelist_validation,
    )
    level = assessment["readiness_level"]
    dimensions = assessment["dimensions"]
    coverage = dimensions["mapping_coverage"]
    codelist = dimensions["codelist_conformance"]

    gtin = extract_gtin(jsonld_data) or "unknown"
    product_name = extract_product_name(jsonld_data) or "—"
    product_id = str(jsonld_data.get("@id") or "—")

    codelist_counts_html = (
        "".join(
            f"<tr><th scope='row'>{escape(status)}</th><td>{count}</td></tr>"
            for status, count in sorted(codelist.get("counts", {}).items())
        )
        or "<tr><td colspan='2'>Not evaluated in this conversion.</td></tr>"
    )
    formatted_jsonld = json.dumps(jsonld_data, indent=2, ensure_ascii=False)
    generated_html = (
        f"<p class='muted'>{escape(generated_note)}</p>" if generated_note else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Product report — GTIN {escape(gtin)}</title>
<style>{_css()}</style>
</head>
<body>
<header>
  <p class="eyebrow">GDSN to GS1 JSON-LD — product report</p>
  <h1>{escape(product_name)}</h1>
  <p class="muted">GTIN {escape(gtin)} · <code>{escape(product_id)}</code></p>
  {generated_html}
</header>

<h2>DPP readiness — traceability &amp; structural signals</h2>
<p>
  Overall level:
  <span class="level-badge" style="background:{_LEVEL_COLORS.get(level, _TOKENS['text_secondary'])}">
    {escape(level.replace('_', ' '))}
  </span>
</p>
<table>
  <thead><tr><th>Dimension</th><th>Status</th><th>Detail</th></tr></thead>
  <tbody>{_dimension_rows_html(dimensions)}</tbody>
</table>
<p class="muted">{escape(assessment['scope_note'])}</p>

<h2>Mapping evidence summary</h2>
<table>
  <tbody>
    <tr><th scope="row">Profile rows found in source</th>
        <td>{coverage['mapped_count']}/{coverage['profile_row_count']}</td></tr>
    <tr><th scope="row">Populated source elements outside the profile</th>
        <td>{coverage['unmapped_source_element_count']}</td></tr>
    <tr><th scope="row">Structural validation</th>
        <td>{dimensions['structural_validation']['error_count']} error(s),
            {dimensions['structural_validation']['warning_count']} warning(s)</td></tr>
  </tbody>
</table>

<h2>Codelist validation counts</h2>
<table><tbody>{codelist_counts_html}</tbody></table>

<h2>Generated GS1 Web Vocabulary JSON-LD</h2>
<pre>{escape(formatted_jsonld)}</pre>

<footer>
  <p>{escape(_GOVERNANCE_FOOTER)}</p>
  <p>{escape(assessment['scope_note'])}</p>
</footer>
</body>
</html>
"""


def product_report_bytes(html: str) -> bytes:
    return html.encode("utf-8")
