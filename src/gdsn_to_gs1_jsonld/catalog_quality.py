"""Validate mapping catalog governance and YAML/catalog alignment."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import yaml

from .mapping_loader import load_mapping

REQUIRED_CATALOG_COLUMNS = {
    "mapping_version",
    "scope_group",
    "gdsn_bms_id",
    "gdsn_attribute_name",
    "gdsn_xpath",
    "gdsn_module",
    "gdsn_datatype",
    "gdsn_cardinality",
    "code_list",
    "canonical_field",
    "jsonld_property",
    "jsonld_structure",
    "jsonld_object_type",
    "technical_mapping_file",
    "mapping_status",
    "confidence",
    "notes",
    "source",
    "webvoc_property_status",
    "webvoc_property_validation",
    "recommended_jsonld_property",
    "review_action",
}

ALLOWED_MAPPING_STATUSES = {
    "mapped",
    "mapped_official_bms_xpath",
    "mapped_needs_bms_review",
    "candidate",
    "candidate_needs_code_filter_review",
    "candidate_official_bms_xpath",
    "candidate_needs_webvoc_review",
    "needs_bms_review",
    "needs_semantic_review",
    "needs_web_vocab_review",
    "needs_webvoc_review",
    "unsupported",
    "out_of_scope",
    "experimental",
    "review_replace",
    "model_review",
}

ALLOWED_CONFIDENCE = {"high", "medium", "low"}

REPORT_LIST_KEYS = (
    "errors",
    "warnings",
    "info",
    "yaml_coverage",
    "catalog_coverage",
    "missing_from_catalog",
    "missing_from_yaml",
    "experimental_mappings",
    "needs_review",
    "webvoc_issues",
)

_PROPERTY_PATTERN = re.compile(r"(?:gs1|schema):[A-Za-z][A-Za-z0-9]*")


@dataclass(frozen=True)
class QualityMessage:
    severity: str
    code: str
    message: str
    category: str
    affected_field_property: str
    reason: str
    recommended_action: str
    blocks_release: bool
    canonical_field: str = ""
    mapping_status: str = ""
    source: str = ""


def _empty_report() -> dict[str, Any]:
    report: dict[str, Any] = {"summary": {}}
    report.update({key: [] for key in REPORT_LIST_KEYS})
    return report


def _message(
    severity: str,
    code: str,
    message: str,
    *,
    canonical_field: str = "",
    mapping_status: str = "",
    source: str = "",
) -> dict[str, Any]:
    normalized_severity = {
        "errors": "error",
        "warnings": "warning",
    }.get(severity, severity)
    category, recommended_action = _classify_warning(
        code,
        canonical_field,
        mapping_status,
    )
    return asdict(
        QualityMessage(
            severity=normalized_severity,
            code=code,
            message=message,
            category=category,
            affected_field_property=canonical_field,
            reason=message,
            recommended_action=recommended_action,
            blocks_release=normalized_severity == "error",
            canonical_field=canonical_field,
            mapping_status=mapping_status,
            source=source,
        )
    )


def _classify_warning(
    code: str,
    canonical_field: str,
    mapping_status: str,
) -> tuple[str, str]:
    field = canonical_field.lower()
    if code in {
        "yaml_field_missing_from_catalog",
        "yaml_property_not_aligned",
        "catalog_field_missing_from_yaml",
    }:
        return (
            "yaml_catalog_mismatch",
            "Align YAML and catalog explicitly or document why they differ.",
        )
    if code == "experimental_mapping_documented":
        return (
            "experimental_mapping",
            "Keep the mapping experimental until standards review is complete.",
        )
    if code == "webvoc_review_required":
        if "nutrient" in field:
            category = "nutrient_modelling"
        elif "image" in field:
            category = "image_modelling"
        elif "document" in field or "referenced_file" in field:
            category = "document_dpp_modelling"
        else:
            category = "webvoc_term_missing"
        return (
            category,
            "Review the latest local Web Vocabulary snapshot before changing "
            "the semantic mapping.",
        )
    if code == "missing_official_bms_id" or "bms" in mapping_status.lower():
        return (
            "needs_bms_review",
            "Confirm the official BMS identifier and XPath evidence.",
        )
    if code == "schema_org_fallback":
        return (
            "schema_org_fallback",
            "Keep the external namespace documented and review GS1 alternatives.",
        )
    return (
        "governance_review",
        "Review and document the governance decision; do not auto-fix semantics.",
    )


def _add(
    report: dict[str, Any],
    severity: str,
    code: str,
    message: str,
    **context: str,
) -> None:
    report[severity].append(_message(severity, code, message, **context))


def _finish_report(
    report: dict[str, Any],
    *,
    strict: bool,
    catalog_rows: int = 0,
    yaml_mappings: int = 0,
) -> dict[str, Any]:
    report["summary"] = {
        "catalog_rows": catalog_rows,
        "yaml_mappings": yaml_mappings,
        "errors": len(report["errors"]),
        "warnings": len(report["warnings"]),
        "info": len(report["info"]),
        "strict": strict,
        "valid": not report["errors"] and (not strict or not report["warnings"]),
    }
    return report


def load_catalog(catalog_path: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    """Load a UTF-8 CSV catalog and return rows plus its column names."""
    path = Path(catalog_path)
    if not path.is_file():
        raise FileNotFoundError(f"Catalog file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        rows = [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
        ]
    return rows, columns


def _mapped_or_candidate(status: str) -> bool:
    return status == "mapped" or status == "candidate" or status.startswith(
        ("mapped_", "candidate_")
    )


def _review_text(row: dict[str, str]) -> str:
    return " ".join(
        row.get(key, "")
        for key in (
            "mapping_status",
            "notes",
            "webvoc_property_status",
            "webvoc_property_validation",
            "review_action",
        )
    ).lower()


def _validate_catalog_rows(
    rows: list[dict[str, str]],
    columns: Iterable[str],
    report: dict[str, Any],
) -> None:
    missing_columns = sorted(REQUIRED_CATALOG_COLUMNS - set(columns))
    if missing_columns:
        _add(
            report,
            "errors",
            "missing_required_columns",
            f"Catalog is missing required columns: {', '.join(missing_columns)}",
        )
        return

    critical_keys = [
        (row["technical_mapping_file"], row["canonical_field"])
        for row in rows
        if row["technical_mapping_file"] and row["canonical_field"]
    ]
    for key, count in Counter(critical_keys).items():
        if count > 1:
            _add(
                report,
                "errors",
                "duplicate_critical_key",
                f"Catalog key {key[0]} / {key[1]} occurs {count} times.",
                canonical_field=key[1],
                source=key[0],
            )

    for row_number, row in enumerate(rows, start=2):
        canonical = row["canonical_field"]
        status = row["mapping_status"].lower()
        confidence = row["confidence"].lower()
        source = f"catalog row {row_number}"

        if status not in ALLOWED_MAPPING_STATUSES:
            _add(
                report,
                "warnings",
                "unknown_mapping_status",
                f"Unknown mapping_status '{row['mapping_status']}'.",
                canonical_field=canonical,
                mapping_status=row["mapping_status"],
                source=source,
            )
        if confidence not in ALLOWED_CONFIDENCE:
            _add(
                report,
                "warnings",
                "unknown_confidence",
                f"Unknown confidence '{row['confidence']}'.",
                canonical_field=canonical,
                mapping_status=row["mapping_status"],
                source=source,
            )

        if _mapped_or_candidate(status):
            for field_name in (
                "gdsn_attribute_name",
                "gdsn_xpath",
                "canonical_field",
                "technical_mapping_file",
            ):
                if not row[field_name]:
                    _add(
                        report,
                        "errors",
                        "missing_mapped_value",
                        f"Mapped/candidate row has no {field_name}.",
                        canonical_field=canonical,
                        mapping_status=row["mapping_status"],
                        source=source,
                    )
            if not row["jsonld_property"] and not row["recommended_jsonld_property"]:
                _add(
                    report,
                    "warnings",
                    "missing_jsonld_property",
                    "Mapped/candidate row has no JSON-LD property.",
                    canonical_field=canonical,
                    mapping_status=row["mapping_status"],
                    source=source,
                )

        if (
            confidence == "high"
            and "official" in status
            and not row["gdsn_bms_id"]
        ):
            _add(
                report,
                "warnings",
                "missing_official_bms_id",
                "High-confidence official mapping has no GDSN BMS ID.",
                canonical_field=canonical,
                mapping_status=row["mapping_status"],
                source=source,
            )

        review_text = _review_text(row)
        if (
            "not found" in review_text
            or "needs_webvoc_review" in review_text
            or "needs_web_vocab_review" in review_text
        ):
            issue = {
                "canonical_field": canonical,
                "mapping_status": row["mapping_status"],
                "webvoc_property_status": row["webvoc_property_status"],
                "webvoc_property_validation": row["webvoc_property_validation"],
                "review_action": row["review_action"],
            }
            report["webvoc_issues"].append(issue)
            _add(
                report,
                "warnings",
                "webvoc_review_required",
                "Web Vocabulary validation requires review.",
                canonical_field=canonical,
                mapping_status=row["mapping_status"],
                source=source,
            )

        if "review" in review_text and row not in report["needs_review"]:
            report["needs_review"].append(
                {
                    "canonical_field": canonical,
                    "mapping_status": row["mapping_status"],
                    "review_action": row["review_action"],
                    "notes": row["notes"],
                }
            )


def check_catalog(
    catalog_path: str | Path,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Validate a mapping catalog and return a structured quality report."""
    report = _empty_report()
    try:
        rows, columns = load_catalog(catalog_path)
    except (FileNotFoundError, OSError, UnicodeError, csv.Error) as exc:
        _add(report, "errors", "catalog_load_failed", str(exc), source=str(catalog_path))
        return _finish_report(report, strict=strict)

    return validate_catalog(
        rows,
        columns,
        strict=strict,
        source=str(catalog_path),
    )


def validate_catalog(
    rows: list[dict[str, str]],
    columns: Iterable[str],
    *,
    strict: bool = False,
    source: str = "catalog",
) -> dict[str, Any]:
    """Validate already loaded catalog rows."""
    report = _empty_report()
    _validate_catalog_rows(rows, columns, report)
    if not report["errors"]:
        _add(
            report,
            "info",
            "catalog_loaded",
            f"Validated {len(rows)} catalog rows.",
            source=source,
        )
    return _finish_report(report, strict=strict, catalog_rows=len(rows))


def extract_yaml_mappings(mapping_path: str | Path) -> list[dict[str, Any]]:
    """Flatten simple and object mappings into comparable records."""
    mapping = load_mapping(mapping_path)
    records: list[dict[str, Any]] = []

    for field in mapping.fields:
        records.append(
            {
                "id": field.id,
                "kind": "field",
                "canonical_field": field.canonical_field,
                "jsonld_property": field.jsonld_property,
                "xpath": field.xpath,
                "mapping_file": Path(mapping_path).name,
            }
        )

    for object_mapping in mapping.object_mappings:
        parent_canonical = f"{object_mapping.canonical_field}[]"
        records.append(
            {
                "id": object_mapping.id,
                "kind": "object",
                "canonical_field": parent_canonical,
                "jsonld_property": object_mapping.jsonld_property,
                "xpath": object_mapping.parent_xpath,
                "mapping_file": Path(mapping_path).name,
            }
        )
        for field in object_mapping.fields:
            child_canonical = field.canonical_field or field.id
            records.append(
                {
                    "id": field.id,
                    "kind": "object_field",
                    "canonical_field": f"{parent_canonical}.{child_canonical}",
                    "jsonld_property": field.jsonld_property,
                    "xpath": field.xpath,
                    "mapping_file": Path(mapping_path).name,
                }
            )
    return records


def _canonical_variants(canonical_field: str) -> set[str]:
    variants = {canonical_field}
    for suffix in (".value", ".unit_code", "_value", "_unit", "_unit_code"):
        if canonical_field.endswith(suffix):
            variants.add(canonical_field[: -len(suffix)])
    if canonical_field.endswith("_code"):
        variants.add(canonical_field[: -len("_code")])
    variants.add(canonical_field.replace("preparation_state_code", "preparation_state"))
    variants.add(canonical_field.replace("nutrient_type_code", "nutrient_type"))
    return {value for value in variants if value}


def _canonical_aligned(yaml_field: str, catalog_field: str) -> bool:
    yaml_variants = _canonical_variants(yaml_field)
    catalog_variants = _canonical_variants(catalog_field)
    return bool(yaml_variants & catalog_variants)


def _property_tokens(value: str) -> set[str]:
    tokens = set(_PROPERTY_PATTERN.findall(value or ""))
    for token in list(tokens):
        if "." in token:
            tokens.add(token.split(".", 1)[0])
    return tokens


def _properties_aligned(yaml_property: str, row: dict[str, str]) -> bool:
    yaml_tokens = _property_tokens(yaml_property)
    catalog_tokens = _property_tokens(
        f"{row.get('jsonld_property', '')} {row.get('recommended_jsonld_property', '')}"
    )
    return bool(yaml_tokens & catalog_tokens)


def _matching_catalog_rows(
    yaml_mapping: dict[str, Any],
    catalog_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    return [
        row
        for row in catalog_rows
        if _canonical_aligned(yaml_mapping["canonical_field"], row["canonical_field"])
    ]


def _is_experimental(row: dict[str, str]) -> bool:
    text = _review_text(row)
    return (
        "experimental" in text
        or row.get("review_action", "").lower() == "model_review"
    )


def check_mapping(
    mapping_path: str | Path,
    catalog_path: str | Path,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Compare an executable YAML mapping with catalog governance rows."""
    report = _empty_report()
    try:
        catalog_rows, columns = load_catalog(catalog_path)
    except (FileNotFoundError, OSError, UnicodeError, csv.Error) as exc:
        _add(report, "errors", "catalog_load_failed", str(exc), source=str(catalog_path))
        return _finish_report(report, strict=strict)

    _validate_catalog_rows(catalog_rows, columns, report)
    if REQUIRED_CATALOG_COLUMNS - set(columns):
        return _finish_report(
            report,
            strict=strict,
            catalog_rows=len(catalog_rows),
        )
    try:
        yaml_mappings = extract_yaml_mappings(mapping_path)
    except (FileNotFoundError, OSError, ValueError, yaml.YAMLError) as exc:
        _add(report, "errors", "mapping_load_failed", str(exc), source=str(mapping_path))
        return _finish_report(
            report,
            strict=strict,
            catalog_rows=len(catalog_rows),
        )

    matched_catalog_fields: set[str] = set()
    experimental_seen: set[tuple[str, str]] = set()

    for yaml_mapping in yaml_mappings:
        matches = _matching_catalog_rows(yaml_mapping, catalog_rows)
        aligned_matches = [
            row
            for row in matches
            if _properties_aligned(yaml_mapping["jsonld_property"], row)
        ]
        coverage = {
            **yaml_mapping,
            "catalog_matches": len(matches),
            "property_aligned": bool(aligned_matches),
        }
        report["yaml_coverage"].append(coverage)

        if not matches:
            report["missing_from_catalog"].append(yaml_mapping)
            _add(
                report,
                "warnings",
                "yaml_field_missing_from_catalog",
                "YAML canonical field was not found in the catalog.",
                canonical_field=yaml_mapping["canonical_field"],
                source=yaml_mapping["mapping_file"],
            )
        elif not aligned_matches:
            _add(
                report,
                "warnings",
                "yaml_property_not_aligned",
                "YAML JSON-LD property was not found in catalog property choices.",
                canonical_field=yaml_mapping["canonical_field"],
                source=yaml_mapping["mapping_file"],
            )
        else:
            _add(
                report,
                "info",
                "mapping_aligned",
                "YAML mapping is aligned with a catalog row.",
                canonical_field=yaml_mapping["canonical_field"],
                source=yaml_mapping["mapping_file"],
            )

        for row in matches:
            matched_catalog_fields.add(row["canonical_field"])
            if _is_experimental(row):
                key = (yaml_mapping["canonical_field"], yaml_mapping["jsonld_property"])
                if key not in experimental_seen:
                    experimental_seen.add(key)
                    item = {
                        "canonical_field": yaml_mapping["canonical_field"],
                        "jsonld_property": yaml_mapping["jsonld_property"],
                        "mapping_status": row["mapping_status"],
                        "notes": row["notes"],
                    }
                    report["experimental_mappings"].append(item)
                    _add(
                        report,
                        "info",
                        "experimental_mapping_documented",
                        "Experimental mapping is documented by the catalog.",
                        canonical_field=yaml_mapping["canonical_field"],
                        mapping_status=row["mapping_status"],
                        source=yaml_mapping["mapping_file"],
                    )

        if (
            not matches
            and yaml_mapping["jsonld_property"] == "gs1:referencedDocument"
        ):
            item = {
                "canonical_field": yaml_mapping["canonical_field"],
                "jsonld_property": yaml_mapping["jsonld_property"],
                "mapping_status": "experimental",
                "notes": "Project extension not present as a catalog field row.",
            }
            report["experimental_mappings"].append(item)
            _add(
                report,
                "info",
                "experimental_mapping_documented",
                "Experimental referenced-document parent property is documented.",
                canonical_field=yaml_mapping["canonical_field"],
                mapping_status="experimental",
                source=yaml_mapping["mapping_file"],
            )

    for row in catalog_rows:
        status = row["mapping_status"].lower()
        covered = row["canonical_field"] in matched_catalog_fields
        report["catalog_coverage"].append(
            {
                "canonical_field": row["canonical_field"],
                "technical_mapping_file": row["technical_mapping_file"],
                "mapping_status": row["mapping_status"],
                "confidence": row["confidence"],
                "covered_by_yaml": covered,
            }
        )
        should_be_mapped = status.startswith("mapped") or row["confidence"].lower() == "high"
        if (
            should_be_mapped
            and status not in {"out_of_scope", "unsupported"}
            and not covered
        ):
            missing = {
                "canonical_field": row["canonical_field"],
                "jsonld_property": row["jsonld_property"],
                "technical_mapping_file": row["technical_mapping_file"],
                "mapping_status": row["mapping_status"],
                "confidence": row["confidence"],
            }
            report["missing_from_yaml"].append(missing)
            _add(
                report,
                "warnings",
                "catalog_field_missing_from_yaml",
                "Mapped/high-confidence catalog field was not found in YAML.",
                canonical_field=row["canonical_field"],
                mapping_status=row["mapping_status"],
                source=row["technical_mapping_file"],
            )

    return _finish_report(
        report,
        strict=strict,
        catalog_rows=len(catalog_rows),
        yaml_mappings=len(yaml_mappings),
    )


def quality_report_xlsx_bytes(report: dict[str, Any]) -> bytes:
    """Render a quality report as a multi-sheet Excel workbook."""
    sheets = {
        "Summary": [report["summary"]],
        "Errors": report["errors"],
        "Warnings": report["warnings"],
        "YAML Coverage": report["yaml_coverage"],
        "Catalog Coverage": report["catalog_coverage"],
        "Missing From Catalog": report["missing_from_catalog"],
        "Missing From YAML": report["missing_from_yaml"],
        "Experimental Mappings": report["experimental_mappings"],
        "Needs Review": report["needs_review"],
        "WebVoc Issues": report["webvoc_issues"],
    }
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, rows in sheets.items():
            pd.DataFrame(rows).to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()


def write_quality_reports(
    report: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write JSON and Excel quality reports to an output directory."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": directory / "mapping_quality_report.json",
        "xlsx": directory / "mapping_quality_report.xlsx",
    }
    paths["json"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["xlsx"].write_bytes(quality_report_xlsx_bytes(report))
    return paths
