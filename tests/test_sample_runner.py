import json
from pathlib import Path

import openpyxl
import pytest

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.sample_runner import convert_sample_corpus


SAMPLE_NAMES = {
    "minimal_product.xml",
    "food_product_full.xml",
    "certified_product_with_documents.xml",
    "partially_mapped_product.xml",
}


@pytest.mark.parametrize("sample_name", sorted(SAMPLE_NAMES))
def test_all_samples_convert_with_v0_3(
    sample_dir,
    mapping_v0_3_path,
    sample_name,
):
    result = convert_xml_to_jsonld(sample_dir / sample_name, mapping_v0_3_path)

    assert result.validation_report["valid"] is True
    assert result.jsonld_data["@id"].startswith("https://id.gs1.org/01/")


def test_minimal_sample_does_not_require_food_or_certification(
    sample_dir,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(
        sample_dir / "minimal_product.xml",
        mapping_v0_3_path,
    )

    assert "gs1:ingredientStatement" not in result.jsonld_data
    assert "gs1:hasAllergen" not in result.jsonld_data
    assert "gs1:nutrientDetail" not in result.jsonld_data
    assert "gs1:certification" not in result.jsonld_data
    assert "gs1:referencedDocument" not in result.jsonld_data


def test_food_sample_contains_food_jsonld(sample_dir, mapping_v0_3_path):
    result = convert_xml_to_jsonld(
        sample_dir / "food_product_full.xml",
        mapping_v0_3_path,
    )

    assert len(result.jsonld_data["gs1:ingredientStatement"]) == 2
    assert result.jsonld_data["gs1:hasAllergen"][0]["gs1:allergenType"] == "AN"
    assert len(result.jsonld_data["gs1:nutrientDetail"]) == 2


def test_certified_sample_contains_certification_and_documents(
    sample_dir,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(
        sample_dir / "certified_product_with_documents.xml",
        mapping_v0_3_path,
    )

    assert result.jsonld_data["gs1:certification"][0][
        "schema:identifier"
    ] == "EXAMPLE-CERT-001"
    document_types = {
        item["schema:additionalType"]
        for item in result.jsonld_data["gs1:referencedDocument"]
    }
    assert document_types == {"DPP_DOCUMENT", "CERTIFICATION_DOCUMENT"}


def test_partially_mapped_sample_has_contextual_unmapped_report(
    sample_dir,
    mapping_v0_3_path,
):
    result = convert_xml_to_jsonld(
        sample_dir / "partially_mapped_product.xml",
        mapping_v0_3_path,
    )
    items = {
        item["element"]: item
        for item in result.unmapped_fields["unmapped_elements"]
    }

    assert result.validation_report["valid"] is True
    assert items["consumerStorageInstructions"]["context"]["languageCode"] == "en"
    assert items["nutrientSourceCode"]["context"]["nutrientTypeCode"] == "PRO-"
    assert items["allergenStatement"]["context"]["allergenTypeCode"] == "AM"
    assert items["certificationStatusCode"]["context"][
        "certificationIdentification"
    ] == "EXAMPLE-PARTIAL-CERT"
    assert items["fileName"]["context"][
        "referencedFileTypeCode"
    ] == "TECHNICAL_DATA_SHEET"


def test_sample_runner_creates_json_and_xlsx_summaries(
    sample_dir,
    mapping_v0_3_path,
    tmp_path,
):
    report = convert_sample_corpus(sample_dir, mapping_v0_3_path, tmp_path)

    assert report.successful is True
    assert {row["sample_file"] for row in report.rows} == SAMPLE_NAMES
    summary = json.loads(report.output_paths["json"].read_text(encoding="utf-8"))
    assert summary["summary"] == {
        "sample_count": 4,
        "successful_count": 4,
        "failed_count": 0,
    }
    assert all(row["conversion_success"] for row in summary["samples"])
    required_fields = {
        "sample_file",
        "detected_gtin",
        "conversion_success",
        "jsonld_output_file",
        "validation_valid",
        "validation_error_count",
        "validation_warning_count",
        "unmapped_element_count",
        "unmapped_unique_element_count",
        "mapped_field_count",
        "notes",
    }
    assert all(required_fields <= row.keys() for row in summary["samples"])
    assert all(
        (tmp_path / f"product_{row['detected_gtin']}.jsonld").is_file()
        for row in summary["samples"]
    )
    assert report.output_paths["xlsx"].is_file()
    workbook = openpyxl.load_workbook(report.output_paths["xlsx"], read_only=True)
    assert workbook.sheetnames == ["Sample Summary"]


def test_sample_runner_reports_xml_parse_failure(
    mapping_v0_3_path,
    tmp_path,
):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "broken.xml").write_text("<tradeItem>", encoding="utf-8")

    report = convert_sample_corpus(input_dir, mapping_v0_3_path, output_dir)

    assert report.successful is False
    assert report.rows[0]["sample_file"] == "broken.xml"
    assert report.rows[0]["failure_stage"] == "xml_parsing"
    assert "Invalid XML" in report.rows[0]["exception_message"]
    assert report.output_paths["json"].is_file()
