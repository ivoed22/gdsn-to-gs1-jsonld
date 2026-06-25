import json
import zipfile
from io import BytesIO

from typer.testing import CliRunner

from gdsn_to_gs1_jsonld.cli import app

runner = CliRunner()


def test_cli_creates_output_files(example_xml_path, mapping_path, tmp_path):
    result = runner.invoke(
        app,
        [
            "convert",
            str(example_xml_path),
            "--mapping",
            str(mapping_path),
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "product_08712345678906.jsonld").is_file()
    assert (tmp_path / "mapping_report_08712345678906.xlsx").is_file()
    assert (tmp_path / "validation_report_08712345678906.json").is_file()
    assert (tmp_path / "unmapped_fields_08712345678906.json").is_file()


def test_cli_converts_with_v0_2_mapping(
    example_xml_path,
    mapping_v0_2_path,
    tmp_path,
):
    result = runner.invoke(
        app,
        [
            "convert",
            str(example_xml_path),
            "--mapping",
            str(mapping_v0_2_path),
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    output = json.loads(
        (tmp_path / "product_08712345678906.jsonld").read_text(encoding="utf-8")
    )
    assert "gs1:ingredientStatement" in output
    assert "gs1:hasAllergen" in output
    assert "gs1:nutrientDetail" in output


def test_cli_converts_with_v0_3_mapping(
    example_xml_path,
    mapping_v0_3_path,
    tmp_path,
):
    result = runner.invoke(
        app,
        [
            "convert",
            str(example_xml_path),
            "--mapping",
            str(mapping_v0_3_path),
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    output = json.loads(
        (tmp_path / "product_08712345678906.jsonld").read_text(encoding="utf-8")
    )
    assert "gs1:certification" in output
    assert "gs1:referencedDocument" in output


def test_cli_check_catalog_passes_current_catalog():
    result = runner.invoke(
        app,
        [
            "check-catalog",
            "--catalog",
            (
                "mapping_catalog/"
                "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
            ),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "0 error(s)" in result.output


def test_cli_check_mapping_creates_quality_reports(
    mapping_v0_3_path,
    tmp_path,
):
    result = runner.invoke(
        app,
        [
            "check-mapping",
            "--mapping",
            str(mapping_v0_3_path),
            "--catalog",
            (
                "mapping_catalog/"
                "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
            ),
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "mapping_quality_report.json").is_file()
    assert (tmp_path / "mapping_quality_report.xlsx").is_file()


def test_cli_convert_samples_creates_summary(
    sample_dir,
    mapping_v0_3_path,
    tmp_path,
):
    result = runner.invoke(
        app,
        [
            "convert-samples",
            "--input-dir",
            str(sample_dir),
            "--mapping",
            str(mapping_v0_3_path),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Sample conversion: 4/4 successful" in result.output
    assert (tmp_path / "sample_conversion_summary.json").is_file()
    assert (tmp_path / "sample_conversion_summary.xlsx").is_file()


def test_cli_convert_batch_creates_summary_and_export(
    sample_dir,
    mapping_v0_3_path,
    tmp_path,
):
    input_zip = tmp_path / "samples.zip"
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "minimal_product.xml",
            (sample_dir / "minimal_product.xml").read_bytes(),
        )
        archive.writestr(
            "food_product_full.xml",
            (sample_dir / "food_product_full.xml").read_bytes(),
        )
    input_zip.write_bytes(buffer.getvalue())
    output_dir = tmp_path / "batch_output"

    result = runner.invoke(
        app,
        [
            "convert-batch",
            "--input-zip",
            str(input_zip),
            "--mapping",
            str(mapping_v0_3_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Batch conversion: 2/2 XML file(s) successful" in result.output
    assert (output_dir / "batch_summary.json").is_file()
    assert (output_dir / "batch_summary.xlsx").is_file()
    assert (output_dir / "batch_export.zip").is_file()
