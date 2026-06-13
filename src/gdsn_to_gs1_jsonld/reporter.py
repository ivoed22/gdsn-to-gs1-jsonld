"""Create JSON and Excel conversion reports."""

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


def json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def mapping_report_xlsx_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="Mapping report")
    return buffer.getvalue()


def write_reports(
    output_dir: str | Path,
    gtin: str,
    jsonld_data: dict[str, Any],
    mapping_rows: list[dict[str, Any]],
    validation_report: dict[str, Any],
    unmapped_fields: dict[str, Any],
) -> dict[str, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "jsonld": directory / f"product_{gtin}.jsonld",
        "mapping_report": directory / f"mapping_report_{gtin}.xlsx",
        "validation_report": directory / f"validation_report_{gtin}.json",
        "unmapped_fields": directory / f"unmapped_fields_{gtin}.json",
    }
    paths["jsonld"].write_bytes(json_bytes(jsonld_data))
    paths["mapping_report"].write_bytes(mapping_report_xlsx_bytes(mapping_rows))
    paths["validation_report"].write_bytes(json_bytes(validation_report))
    paths["unmapped_fields"].write_bytes(json_bytes(unmapped_fields))
    return paths
