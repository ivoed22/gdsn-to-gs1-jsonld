"""Codelist value validation (Track D, v0.20.0).

Loads the normalized codelist registry (built by
:mod:`codelist_importer` from the committed public GDSN codelist workbook)
and validates individual code values against it. Deterministic, offline,
read-only. This module never blocks anything by itself — whether a
validation result is treated as a warning or a hard failure is entirely the
caller's decision (see ``convert_xml_to_jsonld``'s optional
``codelist_registry`` parameter).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_PATH = Path("reference_data") / "normalized" / "gdsn_codelists_r3_1_36.json"

VALIDATION_STATUSES = ("valid", "unknown", "deprecated", "missing", "source_unavailable")


class CodelistRegistryError(ValueError):
    """Raised when the registry file is missing or structurally invalid."""


def load_codelist_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    """Load the normalized codelist registry produced by
    :func:`codelist_importer.write_codelist_registry`."""
    file_path = Path(path)
    if not file_path.is_file():
        raise CodelistRegistryError(f"Codelist registry not found: {file_path}")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "codelists" not in data:
        raise CodelistRegistryError(f"Codelist registry malformed: {file_path}")
    return data


def validate_code_value(
    registry: dict[str, Any],
    codelist_name: str,
    value: str | None,
) -> tuple[str, str]:
    """Validate one code value against the registry.

    Returns
    -------
    tuple[str, str]
        (status, detail). status is one of :data:`VALIDATION_STATUSES`.
    """
    if not value or not str(value).strip():
        return "missing", "No value was provided for this codelist-backed field."

    codelists = registry.get("codelists", {})
    entry = codelists.get(codelist_name)
    if entry is None:
        return (
            "source_unavailable",
            f"Codelist {codelist_name!r} is not present in the imported registry.",
        )

    normalized = str(value).strip().upper()
    for allowed in entry.get("values", []):
        if str(allowed.get("value", "")).strip().upper() == normalized:
            return "valid", f"Matches {codelist_name} value {allowed['value']!r}."

    for deprecated in entry.get("deprecated_values", []):
        if str(deprecated.get("value", "")).strip().upper() == normalized:
            sunset = deprecated.get("sunset_release") or "unknown release"
            return (
                "deprecated",
                f"{value!r} was removed from {codelist_name} (sunset release {sunset}).",
            )

    return "unknown", f"{value!r} is not a recognized value in {codelist_name}."


# Canonical field -> codelist name, for the fields the converter actually
# emits as GDSN codes. Deliberately a curated static table, not derived from
# the mapping registry catalog's `code_list` column: the catalog's
# canonical_field strings predate several YAML field renames (e.g. it says
# "nutrients[].preparation_state" where CanonicalProduct has
# "preparation_state_code", and "certification_documents[].referenced_file_
# type" where the YAML merged that group into "referenced_documents") and one
# row (`product_image_url`) carries a code_list value that is not
# semantically a code field at all. The catalog is governed data this
# project does not edit, so a runtime-enforcement feature is built on a
# separately verified, correct mapping instead of trusting those strings.
# Every entry below has been confirmed against both CanonicalProduct's real
# field names and the imported codelist registry's actual codelist names.
CODELIST_DEPENDENCIES: dict[str, str] = {
    "net_content_unit": "MeasurementUnitCode_GDSN",
    "allergens[].allergen_type": "AllergenTypeCode",
    "allergens[].level_of_containment": "LevelOfContainmentCode",
    "nutrients[].nutrient_type_code": "NutrientTypeCode",
    "nutrients[].preparation_state_code": "PreparationTypeCode",
    "referenced_documents[].referenced_file_type": "ReferencedFileTypeCode",
}


def validate_canonical_product_codelists(
    product_dump: dict[str, Any],
    dependencies: dict[str, str],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate every codelist-backed field found in a serialized
    CanonicalProduct (``product.model_dump()``).

    Supports top-level fields (``"net_content_unit"``) and one level of
    object-mapping nesting (``"allergens[].allergen_type"``), matching the
    compound canonical-field notation already used by the mapping registry
    catalog and mapping_promotion.
    """
    results: list[dict[str, Any]] = []
    for canonical_field, codelist_name in sorted(dependencies.items()):
        if "[]." in canonical_field:
            group_name, sub_field = canonical_field.split("[].", 1)
            items = product_dump.get(group_name) or []
            if not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                value = item.get(sub_field)
                status, detail = validate_code_value(registry, codelist_name, value)
                results.append(
                    {
                        "canonical_field": f"{group_name}[{index}].{sub_field}",
                        "code_list": codelist_name,
                        "value": value,
                        "status": status,
                        "detail": detail,
                    }
                )
        else:
            value = product_dump.get(canonical_field)
            status, detail = validate_code_value(registry, codelist_name, value)
            results.append(
                {
                    "canonical_field": canonical_field,
                    "code_list": codelist_name,
                    "value": value,
                    "status": status,
                    "detail": detail,
                }
            )
    return results
