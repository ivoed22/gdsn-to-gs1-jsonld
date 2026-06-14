import csv
import json
from pathlib import Path

import openpyxl
import yaml

from gdsn_to_gs1_jsonld.catalog_quality import (
    REQUIRED_CATALOG_COLUMNS,
    check_catalog,
    check_mapping,
    load_catalog,
    write_quality_reports,
)

CATALOG = Path(
    "mapping_catalog/"
    "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
)


def _write_catalog(path: Path, **overrides: str) -> None:
    row = {column: "" for column in REQUIRED_CATALOG_COLUMNS}
    row.update(
        {
            "mapping_version": "test",
            "scope_group": "Test",
            "gdsn_bms_id": "1",
            "gdsn_attribute_name": "testElement",
            "gdsn_xpath": "/testElement",
            "gdsn_datatype": "string",
            "gdsn_cardinality": "0..1",
            "canonical_field": "test_field",
            "jsonld_property": "schema:name",
            "jsonld_structure": "scalar",
            "technical_mapping_file": "test.yaml",
            "mapping_status": "mapped",
            "confidence": "high",
            "source": "test",
            "webvoc_property_status": "schema_org_only",
            "recommended_jsonld_property": "schema:name",
            "review_action": "OK_schema",
            **overrides,
        }
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED_CATALOG_COLUMNS))
        writer.writeheader()
        writer.writerow(row)


def test_check_catalog_passes_current_v0_3_catalog():
    report = check_catalog(CATALOG)

    assert report["summary"]["valid"] is True
    assert report["summary"]["errors"] == 0
    assert report["summary"]["catalog_rows"] > 0
    assert all(
        {
            "category",
            "affected_field_property",
            "reason",
            "recommended_action",
            "blocks_release",
            "standards_review_required",
        }
        <= set(item)
        for item in report["warnings"]
    )
    categories = {item["category"] for item in report["warnings"]}
    assert {
        "document_dpp_modelling",
        "image_modelling",
        "nutrient_modelling",
        "webvoc_term_missing",
    } <= categories


def test_check_catalog_reports_missing_required_columns(tmp_path):
    catalog = tmp_path / "catalog.csv"
    catalog.write_text("canonical_field,mapping_status\nfield,mapped\n", encoding="utf-8")

    report = check_catalog(catalog)

    assert report["summary"]["valid"] is False
    assert any(item["code"] == "missing_required_columns" for item in report["errors"])


def test_check_catalog_warns_for_invalid_confidence(tmp_path):
    catalog = tmp_path / "catalog.csv"
    _write_catalog(catalog, confidence="certain")

    report = check_catalog(catalog)

    assert report["summary"]["errors"] == 0
    assert any(item["code"] == "unknown_confidence" for item in report["warnings"])


def test_check_catalog_warns_for_unknown_mapping_status(tmp_path):
    catalog = tmp_path / "catalog.csv"
    _write_catalog(catalog, mapping_status="awaiting_committee")

    report = check_catalog(catalog)

    assert report["summary"]["errors"] == 0
    assert any(
        item["code"] == "unknown_mapping_status" for item in report["warnings"]
    )


def test_check_catalog_strict_mode_fails_on_warnings(tmp_path):
    catalog = tmp_path / "catalog.csv"
    _write_catalog(catalog, confidence="certain")

    report = check_catalog(catalog, strict=True)

    assert report["summary"]["errors"] == 0
    assert report["summary"]["warnings"] == 1
    assert report["warnings"][0]["severity"] == "warning"
    assert report["summary"]["valid"] is False


def test_check_mapping_works_with_v0_3_and_reports_experimental(
    mapping_v0_3_path,
):
    report = check_mapping(mapping_v0_3_path, CATALOG)

    assert report["summary"]["valid"] is True
    assert report["summary"]["errors"] == 0
    assert report["summary"]["yaml_mappings"] > 0
    assert any(
        item["jsonld_property"] == "gs1:referencedDocument"
        for item in report["experimental_mappings"]
    )
    assert report["summary"]["warnings"] == 12
    assert all(
        item["recommended_action"]
        and item["blocks_release"] is False
        and item["standards_review_required"] is True
        for item in report["warnings"]
    )
    structural_parents = {
        item["affected_field_property"]
        for item in report["info"]
        if item["code"] == "structural_parent_covered"
    }
    assert structural_parents == {
        "allergens[]",
        "nutrients[]",
        "referenced_documents[]",
    }
    assert all(
        item["category"] == "false_positive_tooling_issue"
        and item["standards_review_required"] is False
        for item in report["info"]
        if item["code"] == "structural_parent_covered"
    )


def test_check_mapping_reports_yaml_field_missing_from_catalog(
    mapping_v0_3_path,
    tmp_path,
):
    mapping_data = yaml.safe_load(mapping_v0_3_path.read_text(encoding="utf-8"))
    mapping_data["fields"].append(
        {
            "id": "uncatalogued",
            "description": "Test-only uncatalogued field",
            "xpath": ".//*[local-name()='uncatalogued']",
            "canonical_field": "uncatalogued",
            "jsonld_property": "schema:additionalProperty",
        }
    )
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text(yaml.safe_dump(mapping_data, sort_keys=False), encoding="utf-8")

    report = check_mapping(mapping, CATALOG)

    assert any(
        item["canonical_field"] == "uncatalogued"
        for item in report["missing_from_catalog"]
    )


def test_object_parent_requires_all_children_to_be_catalogued(
    mapping_v0_3_path,
    tmp_path,
):
    rows, columns = load_catalog(CATALOG)
    rows = [
        row
        for row in rows
        if row["canonical_field"] != "referenced_documents[].document_url"
    ]
    catalog = tmp_path / "partial_catalog.csv"
    with catalog.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    report = check_mapping(mapping_v0_3_path, catalog)

    assert any(
        item["affected_field_property"] == "referenced_documents[]"
        and item["code"] == "yaml_field_missing_from_catalog"
        for item in report["warnings"]
    )


def test_check_mapping_reports_invalid_catalog_and_yaml(tmp_path):
    incomplete_catalog = tmp_path / "incomplete.csv"
    incomplete_catalog.write_text(
        "canonical_field,mapping_status\nfield,mapped\n",
        encoding="utf-8",
    )
    invalid_mapping = tmp_path / "invalid.yaml"
    invalid_mapping.write_text("fields: [", encoding="utf-8")

    catalog_report = check_mapping(invalid_mapping, incomplete_catalog)
    assert any(
        item["code"] == "missing_required_columns"
        for item in catalog_report["errors"]
    )

    valid_catalog = tmp_path / "catalog.csv"
    _write_catalog(valid_catalog)
    yaml_report = check_mapping(invalid_mapping, valid_catalog)
    assert any(item["code"] == "mapping_load_failed" for item in yaml_report["errors"])


def test_write_quality_reports_creates_json_and_xlsx(
    mapping_v0_3_path,
    tmp_path,
):
    report = check_mapping(mapping_v0_3_path, CATALOG)

    paths = write_quality_reports(report, tmp_path)

    saved_report = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert saved_report["summary"] == report["summary"]
    assert paths["xlsx"].is_file()
    workbook = openpyxl.load_workbook(paths["xlsx"], read_only=True)
    assert workbook.sheetnames == [
        "Summary",
        "Errors",
        "Warnings",
        "YAML Coverage",
        "Catalog Coverage",
        "Missing From Catalog",
        "Missing From YAML",
        "Experimental Mappings",
        "Needs Review",
        "WebVoc Issues",
    ]
