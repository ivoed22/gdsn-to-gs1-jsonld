"""Revalidate mapping catalog vocabulary references against local snapshots."""

from __future__ import annotations

import csv
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from .catalog_quality import load_catalog
from .webvoc_monitor import load_linktypes, load_webvoc_jsonld

_PROPERTY_PATTERN = re.compile(r"(?:gs1|schema):[A-Za-z][A-Za-z0-9]*")


def _labels(term: dict[str, Any]) -> str:
    label = term.get("rdfs:label") or term.get("schema:name")
    if isinstance(label, list):
        label = label[0] if label else ""
    if isinstance(label, dict):
        label = label.get("@value", "")
    return str(label or "")


def _ranges(term: dict[str, Any]) -> str:
    value = term.get("schema:rangeIncludes") or term.get("rdfs:range")
    values = value if isinstance(value, list) else [value]
    result = []
    for item in values:
        if isinstance(item, dict) and item.get("@id"):
            result.append(str(item["@id"]))
        elif isinstance(item, str):
            result.append(item)
    return ", ".join(result)


def revalidate_mapping_catalog(
    catalog_path: str | Path,
    webvoc_dir: str | Path,
) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    rows, columns = load_catalog(catalog_path)
    directory = Path(webvoc_dir)
    terms = load_webvoc_jsonld(directory / "gs1Voc.jsonld")
    linktypes = load_linktypes(directory / "linktypes.json")
    findings: list[dict[str, Any]] = []
    updated_rows: list[dict[str, str]] = []

    for row in rows:
        updated = dict(row)
        property_text = " ".join(
            (
                row.get("jsonld_property", ""),
                row.get("recommended_jsonld_property", ""),
            )
        )
        tokens = sorted(set(_PROPERTY_PATTERN.findall(property_text)))
        gs1_tokens = [token for token in tokens if token.startswith("gs1:")]
        schema_tokens = [token for token in tokens if token.startswith("schema:")]
        found = [token for token in gs1_tokens if token in terms]
        linktype_tokens = [
            token
            for token in gs1_tokens
            if token.split(":", 1)[1] in linktypes
        ]
        missing = [
            token
            for token in gs1_tokens
            if token not in terms and token not in linktype_tokens
        ]

        if missing:
            status = "needs_webvoc_review"
        elif gs1_tokens and linktype_tokens and not found:
            status = "webvoc_linktype_available"
        elif gs1_tokens:
            status = "webvoc_found"
        elif schema_tokens:
            status = "schema_org_only"
        else:
            status = "not_applicable"

        validation_parts = [f"{token}=found" for token in found]
        validation_parts.extend(
            f"{token}=stable linktype"
            for token in linktype_tokens
            if linktypes[token.split(":", 1)[1]].get("status") == "stable"
        )
        validation_parts.extend(f"{token}=NOT FOUND" for token in missing)
        validation_parts.extend(f"{token}=schema.org" for token in schema_tokens)

        updated["webvoc_property_status"] = status
        updated["webvoc_property_validation"] = "; ".join(validation_parts)
        updated["webvoc_property_label"] = "; ".join(
            f"{token}: {_labels(terms[token])}"
            for token in found
            if _labels(terms[token])
        )
        updated["webvoc_property_range"] = "; ".join(
            f"{token}: {_ranges(terms[token])}"
            for token in found
            if _ranges(terms[token])
        )
        updated_rows.append(updated)

        category = (
            "webvoc_term_missing"
            if missing
            else "webvoc_linktype_available"
            if linktype_tokens
            else "schema_org_fallback"
            if schema_tokens and not gs1_tokens
            else "validated"
        )
        findings.append(
            {
                "canonical_field": row.get("canonical_field", ""),
                "jsonld_property": row.get("jsonld_property", ""),
                "recommended_jsonld_property": row.get(
                    "recommended_jsonld_property",
                    "",
                ),
                "validation_status": status,
                "category": category,
                "found_terms": found,
                "missing_terms": missing,
                "available_linktypes": linktype_tokens,
                "schema_org_terms": schema_tokens,
                "blocks_release": False,
                "recommended_action": (
                    "Standards review required before changing semantic mappings."
                    if missing
                    else "Consider the stable GS1 link type in a reviewed mapping."
                    if linktype_tokens
                    else "No automatic semantic mapping change."
                ),
            }
        )

    summary = {
        "catalog_rows": len(rows),
        "webvoc_terms": len(terms),
        "linktypes": len(linktypes),
        "rows_with_missing_terms": sum(
            bool(item["missing_terms"]) for item in findings
        ),
        "rows_with_available_linktypes": sum(
            bool(item["available_linktypes"]) for item in findings
        ),
        "valid": True,
    }
    return {"summary": summary, "findings": findings}, updated_rows, columns


def _xlsx_bytes(report: dict[str, Any]) -> bytes:
    flattened = [
        {
            **item,
            "found_terms": ", ".join(item["found_terms"]),
            "missing_terms": ", ".join(item["missing_terms"]),
            "available_linktypes": ", ".join(item["available_linktypes"]),
            "schema_org_terms": ", ".join(item["schema_org_terms"]),
        }
        for item in report["findings"]
    ]
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([report["summary"]]).to_excel(
            writer,
            index=False,
            sheet_name="Summary",
        )
        pd.DataFrame(flattened).to_excel(
            writer,
            index=False,
            sheet_name="Revalidation",
        )
    return buffer.getvalue()


def _write_csv(
    path: Path,
    rows: list[dict[str, str]],
    columns: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_catalog_revalidation_outputs(
    report: dict[str, Any],
    rows: list[dict[str, str]],
    columns: list[str],
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": directory / "mapping_catalog_revalidation_report.json",
        "xlsx": directory / "mapping_catalog_revalidation_report.xlsx",
        "csv": (
            directory
            / "gdsn_to_gs1_web_vocabulary_mapping_catalog_revalidated.csv"
        ),
    }
    paths["json"].write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["xlsx"].write_bytes(_xlsx_bytes(report))
    _write_csv(paths["csv"], rows, columns)
    return paths


def write_versioned_revalidated_catalog(
    catalog_path: str | Path,
    rows: list[dict[str, str]],
    columns: list[str],
) -> Path:
    path = (
        Path(catalog_path).parent
        / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_6_revalidated.csv"
    )
    _write_csv(path, rows, columns)
    return path
