"""Typer command line interface."""

from pathlib import Path

import typer

from .converter import convert_xml_to_jsonld
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


if __name__ == "__main__":
    app()
