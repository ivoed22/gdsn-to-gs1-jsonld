"""Convert a directory of XML samples and summarize the results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pydantic import ValidationError

from .converter import ConversionResult, convert_xml_to_jsonld
from .mapping_loader import load_mapping
from .xml_parser import XMLParseError, parse_xml


@dataclass(frozen=True)
class SampleConversionReport:
    rows: list[dict[str, Any]]
    output_paths: dict[str, Path]

    @property
    def successful(self) -> bool:
        return all(row["conversion_success"] for row in self.rows)


def _summary_row(
    sample_file: Path,
    *,
    result: ConversionResult | None = None,
    failure_stage: str = "",
    exception_message: str = "",
) -> dict[str, Any]:
    if result is None:
        return {
            "sample_file": sample_file.name,
            "detected_gtin": "",
            "conversion_success": False,
            "jsonld_output_file": "",
            "validation_valid": False,
            "validation_error_count": 0,
            "validation_warning_count": 0,
            "unmapped_element_count": 0,
            "unmapped_unique_element_count": 0,
            "mapped_field_count": 0,
            "failure_stage": failure_stage,
            "exception_message": exception_message,
            "notes": f"Failed during {failure_stage}.",
        }

    unmapped = result.unmapped_fields["unmapped_elements"]
    validation = result.validation_report
    validation_valid = bool(validation["valid"])
    return {
        "sample_file": sample_file.name,
        "detected_gtin": result.canonical_product.gtin or "",
        "conversion_success": validation_valid,
        "jsonld_output_file": str(result.output_file_paths["jsonld"]),
        "validation_valid": validation_valid,
        "validation_error_count": len(validation["errors"]),
        "validation_warning_count": len(validation["warnings"]),
        "unmapped_element_count": sum(item["count"] for item in unmapped),
        "unmapped_unique_element_count": len(unmapped),
        "mapped_field_count": sum(
            1 for row in result.mapping_report_rows if row["found"]
        ),
        "failure_stage": "" if validation_valid else "validation",
        "exception_message": (
            "" if validation_valid else "; ".join(validation["errors"])
        ),
        "notes": (
            (
                "Converted successfully with "
                f"{len(validation['warnings'])} validation warning(s)."
            )
            if validation_valid and validation["warnings"]
            else (
                "Converted successfully."
                if validation_valid
                else "Conversion completed, but validation failed."
            )
        ),
    }


def _summary_xlsx_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(
            writer,
            index=False,
            sheet_name="Sample Summary",
        )
    return buffer.getvalue()


def _write_summary(
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_dir / "sample_conversion_summary.json",
        "xlsx": output_dir / "sample_conversion_summary.xlsx",
    }
    payload = {
        "summary": {
            "sample_count": len(rows),
            "successful_count": sum(
                1 for row in rows if row["conversion_success"]
            ),
            "failed_count": sum(
                1 for row in rows if not row["conversion_success"]
            ),
        },
        "samples": rows,
    }
    paths["json"].write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["xlsx"].write_bytes(_summary_xlsx_bytes(rows))
    return paths


def convert_sample_corpus(
    input_dir: str | Path,
    mapping_path: str | Path,
    output_dir: str | Path,
) -> SampleConversionReport:
    """Convert all XML files in a directory and write corpus summaries."""
    source_dir = Path(input_dir)
    destination = Path(output_dir)
    sample_files = sorted(source_dir.glob("*.xml"))
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Sample input directory not found: {source_dir}")
    if not sample_files:
        raise ValueError(f"No XML sample files found in: {source_dir}")

    rows: list[dict[str, Any]] = []
    try:
        load_mapping(mapping_path)
    except (FileNotFoundError, OSError, ValueError, yaml.YAMLError) as exc:
        rows = [
            _summary_row(
                sample_file,
                failure_stage="mapping",
                exception_message=str(exc),
            )
            for sample_file in sample_files
        ]
        return SampleConversionReport(rows, _write_summary(rows, destination))

    for sample_file in sample_files:
        try:
            parse_xml(sample_file)
        except XMLParseError as exc:
            rows.append(
                _summary_row(
                    sample_file,
                    failure_stage="xml_parsing",
                    exception_message=str(exc),
                )
            )
            continue

        try:
            result = convert_xml_to_jsonld(
                sample_file,
                mapping_path,
                output_dir=destination,
                write_files=True,
            )
        except (ValidationError, ValueError) as exc:
            rows.append(
                _summary_row(
                    sample_file,
                    failure_stage="conversion",
                    exception_message=str(exc),
                )
            )
            continue
        except OSError as exc:
            rows.append(
                _summary_row(
                    sample_file,
                    failure_stage="output_writing",
                    exception_message=str(exc),
                )
            )
            continue

        rows.append(_summary_row(sample_file, result=result))

    return SampleConversionReport(rows, _write_summary(rows, destination))
