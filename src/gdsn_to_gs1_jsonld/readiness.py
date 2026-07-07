"""Per-product DPP readiness assessment (v0.31.0).

Deterministic, pure functions — no Streamlit dependency — that summarize
*traceability & structural readiness* signals a conversion has already
computed. Nothing here re-validates, re-scores, or invents data: every
number is read from an existing ``ConversionResult`` field
(``validation_report``, ``mapping_report_rows``, ``unmapped_fields``,
``codelist_validation``).

Honesty rules (same pattern as :mod:`builder_expansion_analysis`):

- The DPP-relevance dimension always reports
  ``not_yet_assessed_pending_crosswalk`` — judging which fields matter for
  a Digital Product Passport is the GS1-first DPP Crosswalk's job
  (v0.36.0+, not built), and deriving it now would mean fabricating data.
- There is deliberately **no single numeric score**: any weighting between
  dimensions would be invented. The assessment reports per-dimension
  statuses plus a transparent overall level derived from fixed rules.
- This is never official GS1 validation and never a production compliance
  or EU DPP conformity claim (see :data:`SCOPE_NOTE`).
"""

from __future__ import annotations

from typing import Any

READINESS_LEVELS = ("structurally_ready", "attention_points", "review_required")

DPP_RELEVANCE_NOT_ASSESSED = "not_yet_assessed_pending_crosswalk"

# Shown wherever the assessment is rendered/exported. Wording is
# no-claims-safe: every restricted phrase appears only negated.
SCOPE_NOTE = (
    "Traceability & structural readiness signals only — not official GS1 "
    "validation, no production compliance claim, and no EU DPP conformity "
    "assessment."
)


def _structural_validation_dimension(validation_report: dict[str, Any]) -> dict[str, Any]:
    errors = list(validation_report.get("errors", []))
    warnings = list(validation_report.get("warnings", []))
    if not validation_report.get("valid", False):
        status = "errors"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"
    return {
        "status": status,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "detail": (
            f"{len(errors)} error(s), {len(warnings)} warning(s) from the "
            "converter's structural validation."
        ),
    }


def _mapping_coverage_dimension(
    mapping_report_rows: list[dict[str, Any]],
    unmapped_fields: dict[str, Any],
) -> dict[str, Any]:
    total = len(mapping_report_rows)
    mapped = sum(1 for row in mapping_report_rows if row.get("found"))
    unmapped_elements = len(unmapped_fields.get("unmapped_elements", []))
    status = (
        "full_profile_coverage"
        if mapped == total and unmapped_elements == 0
        else "partial_profile_coverage"
    )
    return {
        "status": status,
        "mapped_count": mapped,
        "profile_row_count": total,
        "unmapped_source_element_count": unmapped_elements,
        "detail": (
            f"{mapped}/{total} profile rows found in the source; "
            f"{unmapped_elements} populated source element(s) outside the "
            "profile."
        ),
    }


def _codelist_conformance_dimension(
    codelist_validation: list[dict[str, Any]],
) -> dict[str, Any]:
    if not codelist_validation:
        return {
            "status": "not_evaluated",
            "counts": {},
            "detail": (
                "Codelist registry not loaded for this run, or no "
                "codelist-backed fields were present."
            ),
        }
    counts: dict[str, int] = {}
    for entry in codelist_validation:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    non_valid = sum(count for status, count in counts.items() if status != "valid")
    return {
        "status": "all_valid" if non_valid == 0 else "issues_found",
        "counts": counts,
        "detail": (
            f"{counts.get('valid', 0)} valid, {non_valid} non-valid "
            "codelist-backed value(s) against the imported GDSN codelist "
            "registry."
        ),
    }


def _dpp_relevance_dimension() -> dict[str, Any]:
    return {
        "status": DPP_RELEVANCE_NOT_ASSESSED,
        "detail": (
            "Which properties matter for a Digital Product Passport is the "
            "GS1-first DPP Crosswalk's job (v0.36.0+, not built). Reporting "
            "anything else here would fabricate a judgment."
        ),
    }


def _overall_level(dimensions: dict[str, dict[str, Any]]) -> str:
    """Fixed, transparent derivation — no invented weights.

    review_required if structural validation has errors; attention_points
    if anything else is non-clean (warnings, partial coverage, codelist
    issues); structurally_ready only when every evaluated dimension is
    clean. The not-yet-assessed DPP-relevance dimension never affects the
    level (it is not evidence in either direction).
    """
    if dimensions["structural_validation"]["status"] == "errors":
        return "review_required"
    if (
        dimensions["structural_validation"]["status"] == "passed_with_warnings"
        or dimensions["mapping_coverage"]["status"] == "partial_profile_coverage"
        or dimensions["codelist_conformance"]["status"] == "issues_found"
    ):
        return "attention_points"
    return "structurally_ready"


def assess_readiness(
    *,
    validation_report: dict[str, Any],
    mapping_report_rows: list[dict[str, Any]],
    unmapped_fields: dict[str, Any],
    codelist_validation: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assess one converted product's traceability & structural readiness.

    All inputs are existing ``ConversionResult`` fields; pass
    ``codelist_validation`` as an empty list (or omit) when the conversion
    ran without a codelist registry — that dimension then reports
    ``not_evaluated`` rather than pretending a clean result.
    """
    dimensions = {
        "structural_validation": _structural_validation_dimension(validation_report),
        "mapping_coverage": _mapping_coverage_dimension(
            mapping_report_rows, unmapped_fields
        ),
        "codelist_conformance": _codelist_conformance_dimension(
            list(codelist_validation or [])
        ),
        "dpp_relevance": _dpp_relevance_dimension(),
    }
    level = _overall_level(dimensions)
    assert level in READINESS_LEVELS, level
    return {
        "readiness_level": level,
        "dimensions": dimensions,
        "scope_note": SCOPE_NOTE,
    }
