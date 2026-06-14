import json
from pathlib import Path

import openpyxl
from typer.testing import CliRunner

import gdsn_to_gs1_jsonld.webvoc_monitor as webvoc_monitor
from gdsn_to_gs1_jsonld.catalog_revalidation import (
    revalidate_mapping_catalog,
    write_catalog_revalidation_outputs,
)
from gdsn_to_gs1_jsonld.cli import app
from gdsn_to_gs1_jsonld.webvoc_monitor import (
    check_webvoc_updates,
    load_linktypes,
    load_webvoc_jsonld,
    sha256_bytes,
    sha256_file,
    write_webvoc_update_reports,
)

runner = CliRunner()
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _write_snapshot(directory: Path) -> None:
    directory.mkdir(parents=True)
    graph = {
        "@context": {},
        "@graph": [
            {
                "@id": "gs1:",
                "owl:versionInfo": "test-1",
                "dc:lastModified": {"@value": "2026-01-01"},
            },
            {
                "@id": "gs1:gtin",
                "@type": "owl:DatatypeProperty",
                "rdfs:label": {"@value": "GTIN"},
            },
            {
                "@id": "gs1:certificationURI",
                "@type": "owl:DatatypeProperty",
            },
        ],
    }
    (directory / "gs1Voc.jsonld").write_text(
        json.dumps(graph),
        encoding="utf-8",
    )
    (directory / "gs1Voc.ttl").write_text(
        "gs1:gtin a owl:DatatypeProperty .\n"
        "gs1:certificationURI a owl:DatatypeProperty .\n",
        encoding="utf-8",
    )
    (directory / "linktypes.json").write_text(
        json.dumps(
            {
                "dpp": {"status": "stable", "title": "DPP"},
                "certificationInfo": {
                    "status": "stable",
                    "title": "Certification Information",
                },
            }
        ),
        encoding="utf-8",
    )
    (directory / "metadata.json").write_text(
        json.dumps({"detected_version": "test-1"}),
        encoding="utf-8",
    )


def test_webvoc_hash_calculation(tmp_path):
    path = tmp_path / "value.txt"
    path.write_bytes(b"webvoc")

    assert sha256_file(path) == sha256_bytes(b"webvoc")
    assert sha256_file(path) != sha256_bytes(b"changed")


def test_repository_snapshot_hashes_match_metadata():
    snapshot = REPOSITORY_ROOT / "webvoc" / "current"
    metadata = json.loads(
        (snapshot / "metadata.json").read_text(encoding="utf-8")
    )

    assert sha256_file(snapshot / "gs1Voc.jsonld") == metadata["jsonld_sha256"]
    assert sha256_file(snapshot / "gs1Voc.ttl") == metadata["ttl_sha256"]
    assert (
        sha256_file(snapshot / "linktypes.json")
        == metadata["linktypes_sha256"]
    )


def test_loads_local_webvoc_and_stable_linktypes(tmp_path):
    snapshot = tmp_path / "snapshot"
    _write_snapshot(snapshot)

    terms = load_webvoc_jsonld(snapshot / "gs1Voc.jsonld")
    linktypes = load_linktypes(snapshot / "linktypes.json")

    assert "gs1:gtin" in terms
    assert linktypes["dpp"]["status"] == "stable"
    assert linktypes["certificationInfo"]["status"] == "stable"


def test_loaders_accept_utf8_bom(tmp_path):
    snapshot = tmp_path / "snapshot"
    _write_snapshot(snapshot)
    for filename in ("gs1Voc.jsonld", "linktypes.json"):
        path = snapshot / filename
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())

    assert "gs1:gtin" in load_webvoc_jsonld(snapshot / "gs1Voc.jsonld")
    assert "dpp" in load_linktypes(snapshot / "linktypes.json")


def test_no_network_update_check_generates_reports(tmp_path):
    snapshot = tmp_path / "snapshot"
    output = tmp_path / "report"
    _write_snapshot(snapshot)

    report = check_webvoc_updates(snapshot, no_network=True)
    paths = write_webvoc_update_reports(report, output)

    assert report["summary"]["network_used"] is False
    assert report["summary"]["changed_sources"] == []
    assert paths["json"].is_file()
    assert paths["xlsx"].is_file()
    workbook = openpyxl.load_workbook(paths["xlsx"], read_only=True)
    assert "Sources" in workbook.sheetnames


def test_update_check_detects_changed_remote_hash(tmp_path, monkeypatch):
    snapshot = tmp_path / "snapshot"
    _write_snapshot(snapshot)
    remote = {
        "jsonld": (snapshot / "gs1Voc.jsonld").read_bytes(),
        "ttl": (snapshot / "gs1Voc.ttl").read_bytes() + b"# changed\n",
        "linktypes": (snapshot / "linktypes.json").read_bytes(),
    }
    by_url = {
        webvoc_monitor.DEFAULT_JSONLD_URL: remote["jsonld"],
        webvoc_monitor.DEFAULT_TTL_URL: remote["ttl"],
        webvoc_monitor.DEFAULT_LINKTYPES_URL: remote["linktypes"],
    }
    monkeypatch.setattr(
        webvoc_monitor,
        "_fetch",
        lambda url: (by_url[url], None),
    )

    report = check_webvoc_updates(snapshot)

    assert report["summary"]["changed_sources"] == ["ttl"]
    ttl_source = next(
        item for item in report["sources"] if item["source"] == "ttl"
    )
    assert ttl_source["local_hash"] != ttl_source["remote_hash"]


def test_revalidation_recognizes_terms_linktypes_and_schema(tmp_path):
    snapshot = tmp_path / "snapshot"
    _write_snapshot(snapshot)
    catalog = tmp_path / "catalog.csv"
    catalog.write_text(
        "canonical_field,jsonld_property,recommended_jsonld_property,"
        "webvoc_property_status,webvoc_property_validation,"
        "webvoc_property_label,webvoc_property_range\n"
        "gtin,gs1:gtin,,,,,\n"
        "dpp_url,schema:url,gs1:dpp,,,,\n"
        "certificate_url,schema:url,gs1:certificationInfo,,,,\n",
        encoding="utf-8",
    )

    report, rows, columns = revalidate_mapping_catalog(catalog, snapshot)
    paths = write_catalog_revalidation_outputs(
        report,
        rows,
        columns,
        tmp_path / "output",
    )

    assert report["summary"]["rows_with_available_linktypes"] == 2
    assert any("gs1:dpp" in item["available_linktypes"] for item in report["findings"])
    assert any(
        "gs1:certificationInfo" in item["available_linktypes"]
        for item in report["findings"]
    )
    assert all(path.is_file() for path in paths.values())


def test_cli_webvoc_no_network_and_revalidation(tmp_path):
    snapshot = tmp_path / "snapshot"
    _write_snapshot(snapshot)
    update_output = tmp_path / "update"
    update_result = runner.invoke(
        app,
        [
            "check-webvoc-updates",
            "--snapshot-dir",
            str(snapshot),
            "--output",
            str(update_output),
            "--no-network",
        ],
    )

    assert update_result.exit_code == 0, update_result.output
    assert (update_output / "webvoc_update_report.json").is_file()

    catalog = tmp_path / "catalog.csv"
    catalog.write_text(
        "canonical_field,jsonld_property,recommended_jsonld_property,"
        "webvoc_property_status,webvoc_property_validation,"
        "webvoc_property_label,webvoc_property_range\n"
        "gtin,gs1:gtin,,,,,\n",
        encoding="utf-8",
    )
    revalidation_output = tmp_path / "revalidation"
    revalidation_result = runner.invoke(
        app,
        [
            "revalidate-mapping-catalog",
            "--catalog",
            str(catalog),
            "--webvoc-dir",
            str(snapshot),
            "--output",
            str(revalidation_output),
        ],
    )

    assert revalidation_result.exit_code == 0, revalidation_result.output
    assert (
        revalidation_output / "mapping_catalog_revalidation_report.json"
    ).is_file()
    assert (
        revalidation_output / "mapping_catalog_revalidation_report.xlsx"
    ).is_file()
    assert (
        revalidation_output
        / "gdsn_to_gs1_web_vocabulary_mapping_catalog_revalidated.csv"
    ).is_file()
