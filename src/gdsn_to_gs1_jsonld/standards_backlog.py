"""Maintained standards-review decision backlog and offline exporters."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

VALID_DECISION_STATUSES = {
    "open",
    "proposed",
    "accepted",
    "rejected",
    "deferred",
}

BACKLOG: tuple[dict[str, Any], ...] = (
    {
        "id": "SDR-001",
        "title": "Nutrient modelling",
        "status": "open",
        "category": "nutrient_modelling",
        "affected_fields": [
            "nutrients[].preparation_state",
            "nutrients[].nutrient_type",
            "nutrients[].quantity_contained",
        ],
        "affected_properties": [
            "gs1:nutrientDetail",
            "gs1:preparationStateCode",
            "gs1:nutrientTypeCode",
            "gs1:quantityContained",
        ],
        "warning_count": 3,
        "blocks_release": False,
        "standards_review_required": True,
        "recommended_owner": "GS1 Web Vocabulary owner and sector experts",
        "target_release": "v0.8.0 or standards-approved mapping release",
        "decision_file": "SDR-001-nutrient-modelling.md",
        "issue_number": 4,
        "issue_url": "https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/4",
    },
    {
        "id": "SDR-002",
        "title": "Document and DPP modelling",
        "status": "open",
        "category": "document_dpp_modelling",
        "affected_fields": [
            "certification_documents[].referenced_file_type",
            "referenced_documents[].referenced_file_type",
        ],
        "affected_properties": [
            "gs1:referencedFileTypeCode",
            "schema:additionalType",
            "gs1:dpp",
            "gs1:certificationInfo",
        ],
        "warning_count": 2,
        "blocks_release": False,
        "standards_review_required": True,
        "recommended_owner": "GS1 Architecture and DPP/data spaces workstream",
        "target_release": "v0.8.0 or deferred",
        "decision_file": "SDR-002-document-dpp-modelling.md",
        "issue_number": 2,
        "issue_url": "https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/2",
    },
    {
        "id": "SDR-003",
        "title": "Image representation",
        "status": "open",
        "category": "image_modelling",
        "affected_fields": ["product_image_url"],
        "affected_properties": ["gs1:productImage", "schema:image"],
        "warning_count": 1,
        "blocks_release": False,
        "standards_review_required": True,
        "recommended_owner": "GS1 Web Vocabulary owner",
        "target_release": "v0.8.0",
        "decision_file": "SDR-003-image-representation.md",
        "issue_number": 5,
        "issue_url": "https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/5",
    },
    {
        "id": "SDR-004",
        "title": "Allergen containment",
        "status": "open",
        "category": "webvoc_term_missing",
        "affected_fields": ["allergens[].level_of_containment"],
        "affected_properties": [
            "gs1:levelOfContainment",
            "gs1:allergenLevelOfContainmentCode",
        ],
        "warning_count": 1,
        "blocks_release": False,
        "standards_review_required": True,
        "recommended_owner": "GS1 Web Vocabulary owner and food sector experts",
        "target_release": "v0.8.0",
        "decision_file": "SDR-004-allergen-containment.md",
        "issue_number": 7,
        "issue_url": "https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/7",
    },
    {
        "id": "SDR-005",
        "title": "Certification semantics",
        "status": "open",
        "category": "certification_semantics",
        "affected_fields": [
            "certifications[].certification_identification",
            "certifications[].certificate_issuance_date_time",
            "certifications[].effective_start",
        ],
        "affected_properties": [
            "schema:identifier",
            "schema:dateIssued",
            "gs1:certificationURI",
            "gs1:certificationValue",
            "gs1:certificationStartDate",
        ],
        "warning_count": 3,
        "blocks_release": False,
        "standards_review_required": True,
        "recommended_owner": "GS1 Web Vocabulary owner and GDSN/GSMP group",
        "target_release": "v0.8.0",
        "decision_file": "SDR-005-certification-semantics.md",
        "issue_number": 8,
        "issue_url": "https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/8",
    },
    {
        "id": "SDR-006",
        "title": "YAML and catalog governance",
        "status": "open",
        "category": "yaml_catalog_mismatch",
        "affected_fields": [
            "certification_documents[].file_name",
            "certification_documents[].document_url",
        ],
        "affected_properties": [
            "schema:name",
            "schema:url",
            "gs1:certificationInfo",
        ],
        "warning_count": 2,
        "blocks_release": False,
        "standards_review_required": True,
        "recommended_owner": "Internal project owner and mapping governance group",
        "target_release": "v0.8.0 or governance decision",
        "decision_file": "SDR-006-yaml-catalog-governance.md",
        "issue_number": 9,
        "issue_url": "https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/9",
    },
)

CSV_COLUMNS = (
    "id",
    "title",
    "status",
    "category",
    "warning_count",
    "blocks_release",
    "standards_review_required",
    "recommended_owner",
    "target_release",
    "decision_file",
    "issue_number",
    "issue_url",
)


def validate_backlog(backlog: tuple[dict[str, Any], ...] = BACKLOG) -> None:
    ids = [item["id"] for item in backlog]
    if len(ids) != len(set(ids)):
        raise ValueError("Standards decision IDs must be unique.")
    invalid = sorted(
        {
            item["status"]
            for item in backlog
            if item["status"] not in VALID_DECISION_STATUSES
        }
    )
    if invalid:
        raise ValueError(f"Invalid standards decision statuses: {invalid}")


def export_standards_backlog(
    output_dir: str | Path,
    *,
    output_format: str = "all",
    warning_review: str | Path | None = None,
) -> dict[str, Path]:
    """Write maintained backlog data without changing detailed SDR files."""
    if output_format not in {"all", "json", "csv"}:
        raise ValueError("--format must be one of: all, json, csv")
    if warning_review is not None and not Path(warning_review).is_file():
        raise FileNotFoundError(f"Warning review not found: {warning_review}")

    validate_backlog()
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    if output_format in {"all", "json"}:
        json_path = directory / "standards_review_backlog.json"
        json_path.write_text(
            json.dumps(BACKLOG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        paths["json"] = json_path

    if output_format in {"all", "csv"}:
        csv_path = directory / "standards_review_backlog.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for item in BACKLOG:
                writer.writerow({column: item[column] for column in CSV_COLUMNS})
        paths["csv"] = csv_path

    return paths
