import json

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
