"""Typer command line interface."""

from pathlib import Path
from typing import Optional

import typer

from .batch_converter import (
    BatchConversionError,
    BatchConversionLimits,
    convert_batch_zip,
)
from .catalog_quality import check_catalog, check_mapping, write_quality_reports
from .catalog_revalidation import (
    revalidate_mapping_catalog,
    write_catalog_revalidation_outputs,
    write_versioned_revalidated_catalog,
)
from .converter import convert_xml_to_jsonld
from .reference_data_importer import (
    DEFAULT_GDSN_XLSX,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_MANIFEST,
    DEFAULT_WEBVOC,
    build_reference_data_import,
    write_reference_data_outputs,
)
from .sample_runner import convert_sample_corpus
from .standards_backlog import BACKLOG, export_standards_backlog
from .webvoc_monitor import (
    DEFAULT_JSONLD_URL,
    DEFAULT_LINKTYPES_URL,
    DEFAULT_TTL_URL,
    check_webvoc_updates,
    write_webvoc_update_reports,
)
from .webvoc_explorer import (
    build_explorer_dataset,
    write_webvoc_explorer_outputs,
)
from .xml_parser import XMLParseError
from .mapping_candidate_generator import (
    build_candidate_inputs,
    filter_candidates,
    generate_all_candidates,
    generate_candidates_for_property,
    generate_candidate_summary,
    write_candidate_reports,
)
from .product_passport_sources import (
    build_product_passport_source_inventory,
    load_product_passport_source_manifest,
    validate_product_passport_source_manifest,
    validate_product_passport_file,
    write_product_passport_inventory_reports,
    write_schema_validation_report,
)

app = typer.Typer(
    help="Convert GDSN product XML to GS1 Web Vocabulary JSON-LD.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """GDSN to GS1 JSON-LD command line tools."""


@app.command()
def convert(
    xml_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="GDSN-like XML product file.",
    ),
    mapping: Path = typer.Option(
        ...,
        "--mapping",
        "-m",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="YAML mapping profile.",
    ),
    output: Path = typer.Option(
        Path("output"),
        "--output",
        "-o",
        help="Directory for generated files.",
    ),
) -> None:
    """Convert one product XML file and write JSON-LD plus reports."""
    try:
        result = convert_xml_to_jsonld(
            xml_file,
            mapping,
            output_dir=output,
            write_files=True,
        )
    except (XMLParseError, FileNotFoundError, ValueError) as exc:
        typer.echo(f"Conversion failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    gtin = result.canonical_product.gtin or "unknown"
    typer.echo(f"Converted product: {gtin}")
    typer.echo(f"Validation: {'valid' if result.validation_report['valid'] else 'failed'}")
    typer.echo(f"Output directory: {output.resolve()}")
    for path in result.output_file_paths.values():
        typer.echo(f"  - {path.name}")

    if not result.validation_report["valid"]:
        for error in result.validation_report["errors"]:
            typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1)


@app.command("convert-samples")
def convert_samples(
    input_dir: Path = typer.Option(
        ...,
        "--input-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Directory containing XML sample files.",
    ),
    mapping: Path = typer.Option(
        ...,
        "--mapping",
        "-m",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="YAML mapping profile.",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Directory for sample outputs and summary reports.",
    ),
) -> None:
    """Convert an XML sample corpus and write JSON and Excel summaries."""
    try:
        report = convert_sample_corpus(input_dir, mapping, output_dir)
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Sample conversion failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for row in report.rows:
        if row["conversion_success"]:
            typer.echo(
                f"Converted {row['sample_file']}: {row['detected_gtin']}"
            )
        else:
            typer.echo(
                f"Failed {row['sample_file']} during "
                f"{row['failure_stage']}: {row['exception_message']}",
                err=True,
            )
    typer.echo(
        f"Sample conversion: "
        f"{sum(row['conversion_success'] for row in report.rows)}/"
        f"{len(report.rows)} successful"
    )
    for path in report.output_paths.values():
        typer.echo(f"  - {path}")
    if not report.successful:
        raise typer.Exit(code=1)


@app.command("convert-batch")
def convert_batch(
    input_zip: Path = typer.Option(
        ...,
        "--input-zip",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="ZIP file containing one or more XML product files.",
    ),
    mapping: Path = typer.Option(
        ...,
        "--mapping",
        "-m",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="YAML mapping profile.",
    ),
    output_dir: Path = typer.Option(
        Path("batch_output"),
        "--output-dir",
        "-o",
        help="Directory for batch summary files and export ZIP.",
    ),
    max_files: int = typer.Option(
        100,
        "--max-files",
        min=1,
        help="Maximum number of XML files to process from the ZIP.",
    ),
    max_file_size_mb: int = typer.Option(
        10,
        "--max-file-size-mb",
        min=1,
        help="Maximum uncompressed size per XML file in MB.",
    ),
    max_total_size_mb: int = typer.Option(
        100,
        "--max-total-size-mb",
        min=1,
        help="Maximum total uncompressed XML payload size in MB.",
    ),
) -> None:
    """Convert all XML files in a ZIP and write a batch export package."""
    limits = BatchConversionLimits(
        max_files=max_files,
        max_uncompressed_file_size=max_file_size_mb * 1024 * 1024,
        max_total_uncompressed_size=max_total_size_mb * 1024 * 1024,
    )
    try:
        report = convert_batch_zip(
            input_zip,
            mapping,
            limits=limits,
            output_dir=output_dir,
        )
    except BatchConversionError as exc:
        typer.echo(f"Batch conversion failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        "Batch conversion: "
        f"{report.success_count}/{report.xml_files_found} XML file(s) successful"
    )
    typer.echo(
        "Validation issues: "
        f"{report.summary['summary']['validation_error_count']} error(s), "
        f"{report.summary['summary']['validation_warning_count']} warning(s)"
    )
    for path in report.output_paths.values():
        typer.echo(f"  - {path}")
    for row in report.summary["files"]:
        if row["status"] == "success":
            typer.echo(
                f"Converted {row['filename']}: "
                f"{row['gtin'] or row['output_name']}"
            )
        else:
            typer.echo(
                f"Failed {row['filename']}: "
                f"{row['error_type']} - {row['error_message']}",
                err=True,
            )
    if report.success_count == 0:
        raise typer.Exit(code=1)


def _print_quality_summary(report: dict, output_paths: dict | None = None) -> None:
    summary = report["summary"]
    typer.echo(
        "Quality check: "
        f"{summary['errors']} error(s), "
        f"{summary['warnings']} warning(s), "
        f"{summary['info']} info message(s)"
    )
    typer.echo(
        f"Catalog rows: {summary['catalog_rows']}; "
        f"YAML mappings: {summary['yaml_mappings']}"
    )
    for error in report["errors"]:
        context = (
            f" ({error['canonical_field']})" if error["canonical_field"] else ""
        )
        typer.echo(
            f"Error [{error['code']}]{context}: {error['message']}",
            err=True,
        )
    for warning in report["warnings"]:
        context = (
            f" ({warning['canonical_field']})"
            if warning["canonical_field"]
            else ""
        )
        typer.echo(f"Warning [{warning['code']}]{context}: {warning['message']}")
    if output_paths:
        for path in output_paths.values():
            typer.echo(f"  - {path}")


@app.command("check-catalog")
def check_catalog_command(
    catalog: Path = typer.Option(..., "--catalog", help="Mapping catalog CSV."),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as a failing result.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional directory for JSON and Excel quality reports.",
    ),
) -> None:
    """Validate mapping catalog structure, statuses, and review metadata."""
    report = check_catalog(catalog, strict=strict)
    output_paths = write_quality_reports(report, output) if output else None
    _print_quality_summary(report, output_paths)
    if not report["summary"]["valid"]:
        raise typer.Exit(code=1)


@app.command("check-mapping")
def check_mapping_command(
    mapping: Path = typer.Option(..., "--mapping", "-m", help="YAML mapping file."),
    catalog: Path = typer.Option(..., "--catalog", help="Mapping catalog CSV."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional directory for JSON and Excel quality reports.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as a failing result.",
    ),
) -> None:
    """Compare YAML mapping fields and properties with catalog rows."""
    report = check_mapping(mapping, catalog, strict=strict)
    output_paths = write_quality_reports(report, output) if output else None
    _print_quality_summary(report, output_paths)
    if not report["summary"]["valid"]:
        raise typer.Exit(code=1)


@app.command("check-webvoc-updates")
def check_webvoc_updates_command(
    snapshot_dir: Path = typer.Option(
        Path("webvoc/current"),
        "--snapshot-dir",
        help="Directory containing the local Web Vocabulary snapshot.",
    ),
    output: Path = typer.Option(
        Path("webvoc_update_report"),
        "--output",
        "-o",
        help="Directory for JSON and Excel update reports.",
    ),
    jsonld_url: str = typer.Option(
        DEFAULT_JSONLD_URL,
        "--jsonld-url",
        help="Official GS1 Web Vocabulary JSON-LD URL.",
    ),
    ttl_url: str = typer.Option(
        DEFAULT_TTL_URL,
        "--ttl-url",
        help="Official GS1 Web Vocabulary Turtle URL.",
    ),
    linktypes_url: str = typer.Option(
        DEFAULT_LINKTYPES_URL,
        "--linktypes-url",
        help="Official GS1 link types JSON URL.",
    ),
    no_network: bool = typer.Option(
        False,
        "--no-network",
        help="Validate only the local snapshot without network access.",
    ),
    update_snapshot: bool = typer.Option(
        False,
        "--update-snapshot",
        help="Replace local snapshots after reporting remote differences.",
    ),
) -> None:
    """Compare official Web Vocabulary resources with a local snapshot."""
    try:
        report = check_webvoc_updates(
            snapshot_dir,
            jsonld_url=jsonld_url,
            ttl_url=ttl_url,
            linktypes_url=linktypes_url,
            no_network=no_network,
            update_snapshot=update_snapshot,
        )
        paths = write_webvoc_update_reports(report, output)
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Web Vocabulary update check failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        "Web Vocabulary update check: "
        f"{len(report['summary']['changed_sources'])} changed source(s)"
    )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("revalidate-mapping-catalog")
def revalidate_mapping_catalog_command(
    catalog: Path = typer.Option(
        ...,
        "--catalog",
        help="Mapping catalog CSV.",
    ),
    webvoc_dir: Path = typer.Option(
        Path("webvoc/current"),
        "--webvoc-dir",
        help="Local Web Vocabulary snapshot directory.",
    ),
    output: Path = typer.Option(
        Path("mapping_catalog_revalidation"),
        "--output",
        "-o",
        help="Directory for revalidation outputs.",
    ),
    write_updated_catalog: bool = typer.Option(
        False,
        "--write-updated-catalog",
        help="Write a new v0.6 revalidated catalog beside the source catalog.",
    ),
) -> None:
    """Revalidate catalog vocabulary terms against local WebVoc snapshots."""
    try:
        report, rows, columns = revalidate_mapping_catalog(
            catalog,
            webvoc_dir,
        )
        paths = write_catalog_revalidation_outputs(
            report,
            rows,
            columns,
            output,
        )
        if write_updated_catalog:
            paths["versioned_catalog"] = write_versioned_revalidated_catalog(
                catalog,
                rows,
                columns,
            )
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Catalog revalidation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    summary = report["summary"]
    typer.echo(
        "Catalog revalidation: "
        f"{summary['rows_with_missing_terms']} row(s) with missing terms; "
        f"{summary['rows_with_available_linktypes']} row(s) with linktypes"
    )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("export-standards-backlog")
def export_standards_backlog_command(
    warning_review: Path = typer.Option(
        Path("docs/warning-cleanup-v0.6.1.md"),
        "--warning-review",
        help="Existing warning review used as the human-readable source context.",
    ),
    output: Path = typer.Option(
        Path("docs/standards-decisions"),
        "--output",
        "-o",
        help="Directory for machine-readable backlog files.",
    ),
    output_format: str = typer.Option(
        "all",
        "--format",
        help="Output format: all, json, or csv.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Reserved for explicit SDR regeneration; detailed SDR files are maintained.",
    ),
) -> None:
    """Export the maintained standards-review backlog without network access."""
    try:
        paths = export_standards_backlog(
            output,
            output_format=output_format.lower(),
            warning_review=warning_review,
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Standards backlog export failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Standards backlog: {len(BACKLOG)} open topic(s), "
        f"{sum(item['warning_count'] for item in BACKLOG)} warning(s)"
    )
    if overwrite:
        typer.echo(
            "Detailed SDR Markdown remains manually maintained; "
            "--overwrite does not replace review records."
        )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("export-webvoc-explorer")
def export_webvoc_explorer_command(
    webvoc: Path = typer.Option(
        Path("webvoc/current/gs1Voc.jsonld"),
        "--webvoc",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Local GS1 Web Vocabulary JSON-LD snapshot.",
    ),
    catalog: Path = typer.Option(
        Path(
            "mapping_catalog/"
            "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
        ),
        "--catalog",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Mapping catalog CSV used for coverage and evidence.",
    ),
    backlog: Path = typer.Option(
        Path("docs/standards-decisions/standards_review_backlog.json"),
        "--backlog",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Standards review backlog JSON used for SDR indicators.",
    ),
    output_dir: Path = typer.Option(
        Path("webvoc_explorer_output"),
        "--output-dir",
        "-o",
        help="Directory for Explorer JSON, CSV, and summary files.",
    ),
) -> None:
    """Export offline Web Vocabulary Explorer data and summaries."""
    try:
        dataset = build_explorer_dataset(
            webvoc_path=webvoc,
            catalog_path=catalog,
            backlog_path=backlog,
            metadata_path=webvoc.parent / "metadata.json",
            linktypes_path=webvoc.parent / "linktypes.json",
        )
        paths = write_webvoc_explorer_outputs(dataset, output_dir)
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Web Vocabulary Explorer export failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    summary = dataset.summary
    typer.echo(
        "Web Vocabulary Explorer: "
        f"{summary['class_count']} class(es), "
        f"{summary['property_count']} properties, "
        f"{summary['mapped_property_count']} mapped properties, "
        f"{summary['standards_review_property_count']} standards-review properties"
    )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("import-reference-data")
def import_reference_data_command(
    gdsn_xlsx: Path = typer.Option(
        DEFAULT_GDSN_XLSX,
        "--gdsn-xlsx",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Public GDSN BMS/XPath Excel workbook.",
    ),
    webvoc: Path = typer.Option(
        DEFAULT_WEBVOC,
        "--webvoc",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Local GS1 Web Vocabulary JSON-LD snapshot.",
    ),
    source_manifest: Path = typer.Option(
        DEFAULT_SOURCE_MANIFEST,
        "--source-manifest",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Source manifest with URLs, checksums, and usage notes.",
    ),
    output_dir: Path = typer.Option(
        DEFAULT_OUTPUT_DIR,
        "--output-dir",
        "-o",
        help="Directory for normalized reference data outputs.",
    ),
) -> None:
    """Normalize public GDSN and Web Vocabulary reference data offline."""
    try:
        import_result = build_reference_data_import(
            gdsn_xlsx=gdsn_xlsx,
            webvoc=webvoc,
            source_manifest=source_manifest,
        )
        paths = write_reference_data_outputs(import_result, output_dir)
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Reference data import failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    summary = import_result.summary
    typer.echo(
        "Reference data import: "
        f"{summary['gdsn']['total_rows']} GDSN row(s), "
        f"{summary['webvoc']['property_count']} WebVoc property row(s), "
        f"{summary['webvoc']['class_count']} WebVoc class(es)"
    )
    typer.echo(
        "GDSN sheet: "
        f"{summary['gdsn']['selected_sheet']} "
        f"({summary['gdsn']['candidate_source_rows']} candidate row(s))"
    )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("generate-mapping-candidates")
def generate_mapping_candidates_command(
    webvoc_properties: Path = typer.Option(
        ...,
        "--webvoc-properties",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Normalized WebVoc properties CSV.",
    ),
    gdsn_reference: Path = typer.Option(
        ...,
        "--gdsn-reference",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Normalized GDSN attributes CSV.",
    ),
    catalog: Path = typer.Option(
        ...,
        "--catalog",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Mapping catalog CSV.",
    ),
    mapping: Path = typer.Option(
        ...,
        "--mapping",
        "-m",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="YAML mapping profile.",
    ),
    standards_backlog: Optional[Path] = typer.Option(
        None,
        "--standards-backlog",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Standards review backlog JSON (optional).",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "-o",
        help="Directory for candidate report outputs.",
    ),
    property_filter: Optional[str] = typer.Option(
        None,
        "--property",
        help="Limit to one WebVoc property term_id, e.g. gs1:gtin.",
    ),
    limit_per_property: int = typer.Option(
        20,
        "--limit-per-property",
        min=1,
        max=200,
        help="Maximum candidate GDSN attributes per WebVoc property.",
    ),
    min_confidence: str = typer.Option(
        "low",
        "--min-confidence",
        help="Minimum confidence level to include: high, medium, low.",
    ),
    include_low_confidence: bool = typer.Option(
        True,
        "--include-low-confidence/--no-include-low-confidence",
        help="Include low-confidence candidates.",
    ),
    include_review_required: bool = typer.Option(
        True,
        "--include-review-required/--no-include-review-required",
        help="Include review_required candidates.",
    ),
    output_format: str = typer.Option(
        "json,csv",
        "--format",
        help="Output formats: comma-separated combination of json, csv, xlsx.",
    ),
) -> None:
    """Propose GDSN/BMS/XPath source fields for GS1 Web Vocabulary properties.

    Candidates are review support only. They do not update mapping YAML or
    converter behavior.  No mappings are automatically accepted or written.
    """
    typer.echo(
        "Mapping Candidate Generator: candidates are review support only. "
        "No mappings are automatically accepted or written."
    )
    try:
        backlog_path = str(standards_backlog) if standards_backlog else None
        inputs = build_candidate_inputs(
            webvoc_path=str(webvoc_properties),
            gdsn_path=str(gdsn_reference),
            catalog_path=str(catalog),
            mapping_path=str(mapping),
            backlog_path=backlog_path,
        )
        if property_filter:
            candidates = generate_candidates_for_property(
                property_filter.strip(),
                inputs,
                limit=limit_per_property,
            )
        else:
            candidates = generate_all_candidates(
                inputs,
                limit_per_property=limit_per_property,
            )

        # Apply confidence filter.
        candidates = filter_candidates(
            candidates,
            min_confidence=min_confidence,
            include_low_confidence=include_low_confidence,
            include_review_required=include_review_required,
        )

        formats = [f.strip().lower() for f in output_format.split(",") if f.strip()]
        paths = write_candidate_reports(candidates, str(output_dir), formats=formats)
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Mapping candidate generation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    summary = generate_candidate_summary(candidates)
    typer.echo(
        f"Mapping candidates: {summary['total_candidates']} total, "
        f"{summary['properties_covered']} properties covered"
    )
    by_conf = summary["by_confidence"]
    typer.echo(
        f"Confidence: high={by_conf.get('high', 0)}, "
        f"medium={by_conf.get('medium', 0)}, "
        f"low={by_conf.get('low', 0)}, "
        f"review_required={by_conf.get('review_required', 0)}"
    )
    by_status = summary["by_review_status"]
    typer.echo(
        f"Review status: proposed={by_status.get('proposed', 0)}, "
        f"already_mapped={by_status.get('already_mapped', 0)}, "
        f"review_required={by_status.get('review_required', 0)}, "
        f"not_recommended={by_status.get('not_recommended', 0)}"
    )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("inventory-product-passport-sources")
def inventory_product_passport_sources_command(
    manifest: Path = typer.Option(
        Path("product_passport/reference_sources/source_manifest.json"),
        "--manifest",
        help="Product Passport source manifest JSON.",
    ),
    output_dir: Path = typer.Option(
        Path("product_passport/reference_sources/normalized/"),
        "--output-dir",
        "-o",
        help="Directory for inventory report outputs.",
    ),
    output_format: str = typer.Option(
        "json,csv",
        "--format",
        help="Output formats: comma-separated combination of json, csv.",
    ),
) -> None:
    """Inventory Product Passport reference sources from the source manifest.

    Prototype/reference only. Does not claim official GS1 validation or
    production compliance.
    """
    typer.echo(
        "Product Passport Bridge: source inventory — prototype/reference only. "
        "No official GS1 validation or production compliance claimed."
    )
    try:
        pp_manifest = load_product_passport_source_manifest(str(manifest))
        validation_errors = validate_product_passport_source_manifest(pp_manifest)
        if validation_errors:
            for err in validation_errors:
                typer.echo(f"Manifest warning: {err}", err=True)

        base_dir = str(manifest.parent.parent.parent)  # repo root relative to manifest
        inventory = build_product_passport_source_inventory(
            pp_manifest,
            base_dir=base_dir,
        )
        paths = write_product_passport_inventory_reports(
            inventory,
            str(output_dir),
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Source inventory failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Product Passport source inventory: {inventory['total_sources']} source(s)"
    )
    by_type = inventory.get("sources_by_type", {})
    by_sector = inventory.get("sources_by_sector", {})
    typer.echo(
        "By type: "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items()))
    )
    typer.echo(
        "By sector: "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_sector.items()))
    )
    missing = inventory.get("missing_local_files", [])
    if missing:
        typer.echo(
            f"Missing local files ({len(missing)}): "
            + ", ".join(missing),
            err=True,
        )
    for path in paths.values():
        typer.echo(f"  - {path}")


@app.command("validate-product-passport")
def validate_product_passport_command(
    input_file: Path = typer.Option(
        ...,
        "--input",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Product Passport JSON file to validate.",
    ),
    schema_file: Path = typer.Option(
        ...,
        "--schema",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="JSON Schema file for structural validation.",
    ),
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Optional Product Passport source manifest JSON.",
    ),
    output_dir: Path = typer.Option(
        Path("product_passport/validation_reports/"),
        "--output-dir",
        "-o",
        help="Directory for validation report output.",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        help="Output format: json.",
    ),
) -> None:
    """Validate a Product Passport JSON file against a local JSON Schema.

    Structural validation only. Does not claim official GS1 validation or
    production compliance. Exit 0 on success; non-zero only on tool error.
    """
    typer.echo(
        "Product Passport Bridge: schema validator — prototype/reference only."
    )
    typer.echo(
        "Structural validation only. Not official GS1 validation. "
        "Not production compliance."
    )
    try:
        pp_manifest: dict | None = None
        if manifest is not None and manifest.is_file():
            pp_manifest = load_product_passport_source_manifest(str(manifest))

        report = validate_product_passport_file(
            str(input_file),
            str(schema_file),
            manifest=pp_manifest,
        )
        report_path = write_schema_validation_report(report, str(output_dir))
    except (FileNotFoundError, OSError, ValueError) as exc:
        typer.echo(f"Product Passport validation tool error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    status = report.get("validation_status", "unknown")
    error_count = len(report.get("errors", []))
    typer.echo(f"Validation status: {status}")
    typer.echo(f"Schema: {report.get('schema_title') or report.get('schema_id') or schema_file}")
    typer.echo(f"Errors: {error_count}")
    if error_count:
        for err in report.get("errors", []):
            typer.echo(f"  Error: {err}")
    typer.echo(f"  - {report_path}")
    typer.echo(f"Note: {report.get('prototype_warning', '')}")


if __name__ == "__main__":
    app()
