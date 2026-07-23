"""Validation for extracted canonical products."""

import json
from typing import Any

from .canonical_model import CanonicalProduct
from .mapping_loader import MappingConfig
from .utils import is_valid_gtin


def _expected_gtin_check_digit(value: str) -> str | None:
    if not value.isdigit() or len(value) not in {8, 12, 13, 14}:
        return None
    weighted_sum = sum(
        int(digit) * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(value[:-1]))
    )
    return str((10 - weighted_sum % 10) % 10)


def validate_output_evidence(
    jsonld_data: dict[str, Any],
    unmapped_fields: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return deterministic, machine-readable output/evidence checks."""
    checks: list[dict[str, Any]] = []
    try:
        json.loads(json.dumps(jsonld_data, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        checks.append(
            {
                "code": "JSON_SERIALIZATION",
                "status": "error",
                "message": str(exc),
            }
        )
    else:
        checks.append(
            {
                "code": "JSON_SERIALIZATION",
                "status": "passed",
                "message": "JSON-LD output is syntactically serializable JSON.",
            }
        )

    contexts = jsonld_data.get("@context", [])
    if not isinstance(contexts, list):
        contexts = [contexts]
    official_context = "https://ref.gs1.org/voc/data/gs1Voc.jsonld"
    checks.append(
        {
            "code": "GS1_CONTEXT",
            "status": "passed" if official_context in contexts else "warning",
            "message": (
                "Official GS1 Web Vocabulary context is declared."
                if official_context in contexts
                else "Official GS1 Web Vocabulary context is not declared."
            ),
        }
    )
    occurrence_count = len(unmapped_fields.get("unmapped_values", []))
    checks.append(
        {
            "code": "UNMAPPED_SOURCE_EVIDENCE",
            "status": "passed",
            "count": occurrence_count,
            "message": (
                f"{occurrence_count} populated, non-emitted source value(s) "
                "preserved separately."
            ),
        }
    )
    return checks


def validate_product(
    product: CanonicalProduct,
    mapping: MappingConfig,
    mapping_report_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows_by_id = {row["id"]: row for row in mapping_report_rows}
    checks: list[dict[str, Any]] = []

    for field in mapping.fields:
        row = rows_by_id[field.id]
        if field.required and not row["found"]:
            if field.canonical_field == "gtin":
                errors.append(
                    "Required field 'gtin' was not found. Cannot construct product @id."
                )
            else:
                errors.append(f"Required field '{field.id}' was not found.")
        elif not field.required and not row["found"]:
            warnings.append(f"Optional field '{field.id}' was not found.")
        elif row["status"] in {"transform_error", "validation_error"}:
            message = f"Field '{field.id}': {row['message']}"
            if field.required:
                errors.append(message)
            else:
                warnings.append(message)

    if product.net_content_value is None or product.net_content_unit is None:
        if product.net_content_value is not None or product.net_content_unit is not None:
            warnings.append(
                "Net content is incomplete; both value and unit are required for JSON-LD."
            )

    gtin_row = rows_by_id.get("gtin", {})
    source_gtin = str(gtin_row.get("source_value") or "").strip()
    if source_gtin:
        if is_valid_gtin(source_gtin):
            checks.append(
                {
                    "code": "GTIN_CHECK_DIGIT",
                    "status": "passed",
                    "source_value": source_gtin,
                    "message": "GTIN length, digits, and check digit are valid.",
                }
            )
        else:
            expected = _expected_gtin_check_digit(source_gtin)
            check = {
                "code": "GTIN_CHECK_DIGIT",
                "status": "error",
                "source_value": source_gtin,
                "message": (
                    "Source GTIN has an invalid format or check digit and was "
                    "not emitted."
                ),
            }
            if expected is not None:
                check["expected_check_digit"] = expected
                check["candidate_corrected_gtin"] = source_gtin[:-1] + expected
            checks.append(check)

    return {"valid": not errors, "errors": errors, "warnings": warnings, "checks": checks}
