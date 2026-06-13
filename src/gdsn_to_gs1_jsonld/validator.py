"""Validation for extracted canonical products."""

from typing import Any

from .canonical_model import CanonicalProduct
from .mapping_loader import MappingConfig


def validate_product(
    product: CanonicalProduct,
    mapping: MappingConfig,
    mapping_report_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows_by_id = {row["id"]: row for row in mapping_report_rows}

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

    return {"valid": not errors, "errors": errors, "warnings": warnings}
