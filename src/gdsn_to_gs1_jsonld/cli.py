"""Typer command line interface."""

from pathlib import Path

import typer

from .catalog_quality import check_catalog, check_mapping, write_quality_reports
from .catalog_revalidation import (
    revalidate_mapping_catalog,
    write_catalog_revalidation_outputs,
    write_versioned_revalidated_catalog,
)
from .converter import convert_xml_to_jsonld
from .sample_runner import convert_sample_corpus
from .standards_backlog import BACKLOG, export_standards_backlog
from .webvoc_monitor import (
    DEFAULT_JSONLD_URL,
    DEFAULT_LINKTYPES_URL,
    DEFAULT_TTL_URL,
    check_webvoc_updates,
    write_webvoc_update_reports,
)
from .xml_parser import XMLParseError

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


if __name__ == "__main__":
    app()
