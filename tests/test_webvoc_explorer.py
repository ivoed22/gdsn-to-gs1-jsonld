import json
from pathlib import Path

from typer.testing import CliRunner

from gdsn_to_gs1_jsonld.cli import app
from gdsn_to_gs1_jsonld.webvoc_explorer import (
    COVERAGE_STATUSES,
    build_explorer_dataset,
    extract_classes,
    extract_properties,
    filter_properties,
    group_property,
    load_mapping_catalog,
    load_sdr_backlog,
    load_webvoc_jsonld,
)

ROOT = Path(__file__).resolve().parents[1]
WEBVOC = ROOT / "webvoc" / "current" / "gs1Voc.jsonld"
CATALOG = (
    ROOT
    / "mapping_catalog"
    / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
)
BACKLOG = ROOT / "docs" / "standards-decisions" / "standards_review_backlog.json"


def test_loads_local_webvoc_and_extracts_classes_and_properties():
    data = load_webvoc_jsonld(WEBVOC)
    classes = extract_classes(data)
    properties = extract_properties(data)

    assert len(classes) > 40
    assert len(properties) > 500
    product = next(item for item in classes if item.term_id == "gs1:Product")
    assert product.label == "Product"
    assert "Any item" in product.comment
    gtin = next(item for item in properties if item.term_id == "gs1:gtin")
    assert gtin.label == "GTIN"
    assert "gs1:Product" in gtin.domain
    assert "xsd:string" in gtin.range


def test_grouping_heuristics_cover_common_review_areas():
    assert (
        group_property("gs1:productName", label="Product Name")
        == "Core Product Information"
    )
    assert (
        group_property("gs1:nutrientBasisQuantity", label="Nutrient Basis Quantity")
        == "Nutritional Information"
    )
    assert group_property("gs1:hasAllergen", label="Has Allergen") == "Allergens"
    assert group_property("gs1:certificationInfo", label="Certification Information") == "Certifications"
    assert group_property("gs1:dpp", label="Digital Product Passport") == "Documents and DPP"


def test_catalog_coverage_evidence_and_sdr_references_are_linked():
    dataset = build_explorer_dataset(
        webvoc_path=WEBVOC,
        catalog_path=CATALOG,
        backlog_path=BACKLOG,
    )

    gtin = next(item for item in dataset.properties if item.term_id == "gs1:gtin")
    assert gtin.coverage_status == "high_confidence"
    assert gtin.evidence[0].bms_id == "67"
    assert "/gtin" in gtin.evidence[0].gdsn_xpath

    certification_info = next(
        item for item in dataset.properties if item.term_id == "gs1:certificationInfo"
    )
    assert certification_info.coverage_status in COVERAGE_STATUSES
    assert any(ref.sdr_id in {"SDR-002", "SDR-006"} for ref in certification_info.governance)


def test_filter_properties_search_and_flags_work():
    dataset = build_explorer_dataset(
        webvoc_path=WEBVOC,
        catalog_path=CATALOG,
        backlog_path=BACKLOG,
    )

    searched = filter_properties(dataset.properties, search="gtin")
    assert any(item.term_id == "gs1:gtin" for item in searched)
    xpath_searched = filter_properties(dataset.properties, search="/gtin")
    assert any(item.term_id == "gs1:gtin" for item in xpath_searched)
    bms_searched = filter_properties(dataset.properties, search="3733")
    assert any(item.term_id == "gs1:netContent" for item in bms_searched)
    mapped = filter_properties(dataset.properties, only_mapped=True)
    assert mapped
    assert all(item.coverage_status in {"mapped", "high_confidence"} for item in mapped)
    review = filter_properties(dataset.properties, only_standards_review=True)
    assert any(item.governance for item in review)


def test_sdr_governance_links_use_exact_affected_fields():
    dataset = build_explorer_dataset(
        webvoc_path=WEBVOC,
        catalog_path=CATALOG,
        backlog_path=BACKLOG,
    )

    preparation = next(
        item for item in dataset.properties if item.term_id == "gs1:preparationCode"
    )
    assert any(ref.sdr_id == "SDR-001" for ref in preparation.governance)

    allergen = next(
        item for item in dataset.properties if item.term_id == "gs1:hasAllergen"
    )
    assert any(ref.sdr_id == "SDR-004" for ref in allergen.governance)


def test_missing_optional_metadata_is_handled_gracefully(tmp_path):
    webvoc = tmp_path / "mini.jsonld"
    catalog = tmp_path / "catalog.csv"
    webvoc.write_text(
        json.dumps(
            {
                "@graph": [
                    {
                        "@id": "gs1:MiniClass",
                        "@type": ["owl:Class", "rdfs:Class"],
                        "rdfs:label": {"@value": "Mini Class"},
                    },
                    {
                        "@id": "gs1:miniProperty",
                        "@type": ["rdf:Property", "owl:DatatypeProperty"],
                        "rdfs:label": {"@value": "Mini Property"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    catalog.write_text(
        "mapping_version,jsonld_property,mapping_status,confidence\n",
        encoding="utf-8",
    )

    dataset = build_explorer_dataset(
        webvoc_path=webvoc,
        catalog_path=catalog,
        backlog_path=tmp_path / "missing-backlog.json",
        metadata_path=tmp_path / "missing-metadata.json",
        linktypes_path=tmp_path / "missing-linktypes.json",
    )

    assert dataset.summary["webvoc_version"] == ""
    assert dataset.summary["class_count"] == 1
    assert dataset.summary["property_count"] == 1
    assert dataset.properties[0].coverage_status == "unmapped"


def test_loaders_read_catalog_and_sdr_backlog():
    catalog_rows = load_mapping_catalog(CATALOG)
    backlog = load_sdr_backlog(BACKLOG)

    assert len(catalog_rows) >= 20
    assert any(row["jsonld_property"] == "gs1:gtin" for row in catalog_rows)
    assert any(item["id"] == "SDR-001" for item in backlog)


def test_export_webvoc_explorer_cli_creates_outputs(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "export-webvoc-explorer",
            "--webvoc",
            str(WEBVOC),
            "--catalog",
            str(CATALOG),
            "--backlog",
            str(BACKLOG),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Web Vocabulary Explorer:" in result.output
    assert (tmp_path / "webvoc_explorer_properties.json").is_file()
    assert (tmp_path / "webvoc_explorer_properties.csv").is_file()
    assert (tmp_path / "webvoc_explorer_summary.json").is_file()
    assert (tmp_path / "webvoc_explorer_summary.xlsx").is_file()
