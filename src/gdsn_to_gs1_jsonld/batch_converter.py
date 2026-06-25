"""Batch ZIP conversion helpers for GDSN XML product files."""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

import pandas as pd

from .converter import convert_xml_to_jsonld
from .reporter import json_bytes, mapping_report_xlsx_bytes


DEFAULT_MAX_FILES = 100
DEFAULT_MAX_UNCOMPRESSED_FILE_SIZE = 10 * 1024 * 1024
DEFAULT_MAX_TOTAL_UNCOMPRESSED_SIZE = 100 * 1024 * 1024


class BatchConversionError(ValueError):
    """Raised when a ZIP cannot be processed as a batch."""


@dataclass(frozen=True)
class BatchConversionLimits:
    max_files: int = DEFAULT_MAX_FILES
    max_uncompressed_file_size: int = DEFAULT_MAX_UNCOMPRESSED_FILE_SIZE
    max_total_uncompressed_size: int = DEFAULT_MAX_TOTAL_UNCOMPRESSED_SIZE


@dataclass(frozen=True)
class BatchFileResult:
    original_filename: str
    safe_filename: str
    status: str
    output_base_name: str = ""
    gtin: str = ""
    mapped_count: int = 0
    unmapped_count: int = 0
    validation_status: str = ""
    validation_error_count: int = 0
    validation_warning_count: int = 0
    error_type: str = ""
    error_message: str = ""

    def to_summary_row(self) -> dict[str, Any]:
        return {
            "filename": self.original_filename,
            "safe_filename": self.safe_filename,
            "status": self.status,
            "gtin": self.gtin,
            "output_name": self.output_base_name,
            "mapped_count": self.mapped_count,
            "unmapped_count": self.unmapped_count,
            "validation_status": self.validation_status,
            "validation_error_count": self.validation_error_count,
            "validation_warning_count": self.validation_warning_count,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }

    def to_preview_row(self) -> dict[str, Any]:
        gtin_or_output = self.gtin or self.output_base_name
        error_summary = (
            f"{self.error_type}: {self.error_message}"
            if self.error_type and self.error_message
            else self.error_message
        )
        return {
            "filename": self.original_filename,
            "status": self.status,
            "GTIN/output name": gtin_or_output,
            "mapped count": self.mapped_count,
            "unmapped count": self.unmapped_count,
            "validation status": self.validation_status,
            "error summary": error_summary,
        }


@dataclass(frozen=True)
class _BatchArtifact:
    result: BatchFileResult
    jsonld_bytes: bytes | None = None
    mapping_report_bytes: bytes | None = None
    validation_report_bytes: bytes | None = None
    unmapped_fields_bytes: bytes | None = None
    error_bytes: bytes | None = None


@dataclass(frozen=True)
class BatchConversionReport:
    files: list[BatchFileResult]
    summary: dict[str, Any]
    summary_json_bytes: bytes
    summary_xlsx_bytes: bytes
    export_zip_bytes: bytes
    output_paths: dict[str, Path] = field(default_factory=dict)

    @property
    def xml_files_found(self) -> int:
        return int(self.summary["summary"]["xml_files_found"])

    @property
    def success_count(self) -> int:
        return int(self.summary["summary"]["successful_conversions"])

    @property
    def failure_count(self) -> int:
        return int(self.summary["summary"]["failed_conversions"])

    @property
    def preview_rows(self) -> list[dict[str, Any]]:
        return [result.to_preview_row() for result in self.files]


def _read_zip_source(zip_source: bytes | bytearray | str | Path) -> bytes | Path:
    if isinstance(zip_source, (bytes, bytearray)):
        return bytes(zip_source)
    return Path(zip_source)


def _safe_zip_path(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized.strip() or normalized.startswith("/") or path.is_absolute():
        return False
    return all(part not in {"", ".", ".."} and ":" not in part for part in path.parts)


def _safe_filename(name: str, fallback: str = "file") -> str:
    base_name = PurePosixPath(name.replace("\\", "/")).name or fallback
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._-")
    return safe or fallback


def _safe_stem(name: str, fallback: str = "file") -> str:
    return Path(_safe_filename(name, fallback=fallback)).stem or fallback


def _unique_name(base_name: str, used_names: set[str]) -> str:
    candidate = base_name
    suffix = 2
    while candidate in used_names:
        candidate = f"{base_name}_{suffix}"
        suffix += 1
    used_names.add(candidate)
    return candidate


def _validation_status(validation_report: dict[str, Any]) -> str:
    if not validation_report.get("valid"):
        return "invalid"
    if validation_report.get("warnings"):
        return "warnings"
    return "valid"


def _summary_xlsx_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(
            writer,
            index=False,
            sheet_name="Batch Summary",
        )
    return buffer.getvalue()


def _error_artifact(result: BatchFileResult) -> bytes:
    return json_bytes(
        {
            "filename": result.original_filename,
            "safe_filename": result.safe_filename,
            "status": result.status,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }
    )


def _file_error(
    *,
    original_filename: str,
    error_type: str,
    error_message: str,
) -> _BatchArtifact:
    result = BatchFileResult(
        original_filename=original_filename,
        safe_filename=_safe_filename(original_filename),
        status="error",
        error_type=error_type,
        error_message=error_message,
    )
    return _BatchArtifact(result=result, error_bytes=_error_artifact(result))


def _convert_xml_entry(
    *,
    original_filename: str,
    xml_bytes: bytes,
    mapping_path: str | Path,
    used_output_names: set[str],
) -> _BatchArtifact:
    try:
        result = convert_xml_to_jsonld(
            xml_bytes,
            mapping_path,
            write_files=False,
        )
    except Exception as exc:  # noqa: BLE001 - per-file failures must not stop a batch.
        return _file_error(
            original_filename=original_filename,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    gtin = result.canonical_product.gtin or ""
    base_name = _safe_stem(f"product_{gtin}" if gtin else original_filename)
    output_base_name = _unique_name(base_name, used_output_names)
    validation_report = result.validation_report
    unmapped_count = len(result.unmapped_fields.get("unmapped_elements", []))
    file_result = BatchFileResult(
        original_filename=original_filename,
        safe_filename=_safe_filename(original_filename),
        status="success",
        output_base_name=output_base_name,
        gtin=gtin,
        mapped_count=sum(1 for row in result.mapping_report_rows if row.get("found")),
        unmapped_count=unmapped_count,
        validation_status=_validation_status(validation_report),
        validation_error_count=len(validation_report.get("errors", [])),
        validation_warning_count=len(validation_report.get("warnings", [])),
    )
    return _BatchArtifact(
        result=file_result,
        jsonld_bytes=json_bytes(result.jsonld_data),
        mapping_report_bytes=mapping_report_xlsx_bytes(result.mapping_report_rows),
        validation_report_bytes=json_bytes(result.validation_report),
        unmapped_fields_bytes=json_bytes(result.unmapped_fields),
    )


def _build_summary(
    *,
    files: list[BatchFileResult],
    limits: BatchConversionLimits,
) -> dict[str, Any]:
    return {
        "summary": {
            "xml_files_found": len(files),
            "successful_conversions": sum(1 for file in files if file.status == "success"),
            "failed_conversions": sum(1 for file in files if file.status == "error"),
            "total_unmapped_fields": sum(file.unmapped_count for file in files),
            "validation_error_count": sum(file.validation_error_count for file in files),
            "validation_warning_count": sum(
                file.validation_warning_count for file in files
            ),
        },
        "limits": {
            "max_files": limits.max_files,
            "max_uncompressed_file_size": limits.max_uncompressed_file_size,
            "max_total_uncompressed_size": limits.max_total_uncompressed_size,
        },
        "files": [file.to_summary_row() for file in files],
    }


def _build_export_zip(
    artifacts: list[_BatchArtifact],
    summary_json: bytes,
    summary_xlsx: bytes,
) -> bytes:
    used_error_names: set[str] = set()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("batch_summary.json", summary_json)
        archive.writestr("batch_summary.xlsx", summary_xlsx)

        for artifact in artifacts:
            result = artifact.result
            if result.status == "success":
                output_name = result.output_base_name
                archive.writestr(
                    f"products/{output_name}.jsonld",
                    artifact.jsonld_bytes or b"",
                )
                archive.writestr(
                    f"reports/{output_name}_mapping_report.xlsx",
                    artifact.mapping_report_bytes or b"",
                )
                archive.writestr(
                    f"reports/{output_name}_validation_report.json",
                    artifact.validation_report_bytes or b"",
                )
                archive.writestr(
                    f"reports/{output_name}_unmapped_fields.json",
                    artifact.unmapped_fields_bytes or b"",
                )
            else:
                error_name = _unique_name(
                    _safe_stem(result.safe_filename, fallback="file"),
                    used_error_names,
                )
                archive.writestr(
                    f"errors/{error_name}_error.json",
                    artifact.error_bytes or _error_artifact(result),
                )
    return buffer.getvalue()


def _write_outputs(
    output_dir: str | Path,
    *,
    summary_json: bytes,
    summary_xlsx: bytes,
    export_zip: bytes,
) -> dict[str, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary_json": directory / "batch_summary.json",
        "summary_xlsx": directory / "batch_summary.xlsx",
        "export_zip": directory / "batch_export.zip",
    }
    paths["summary_json"].write_bytes(summary_json)
    paths["summary_xlsx"].write_bytes(summary_xlsx)
    paths["export_zip"].write_bytes(export_zip)
    return paths


def convert_batch_zip(
    zip_source: bytes | bytearray | str | Path,
    mapping_path: str | Path,
    *,
    limits: BatchConversionLimits | None = None,
    output_dir: str | Path | None = None,
) -> BatchConversionReport:
    """Convert XML files from a ZIP and return summary plus export ZIP bytes."""
    active_limits = limits or BatchConversionLimits()
    if active_limits.max_files < 1:
        raise BatchConversionError("max_files must be at least 1.")
    if active_limits.max_uncompressed_file_size < 1:
        raise BatchConversionError("max_uncompressed_file_size must be at least 1.")
    if active_limits.max_total_uncompressed_size < 1:
        raise BatchConversionError("max_total_uncompressed_size must be at least 1.")

    zip_input = _read_zip_source(zip_source)
    artifacts: list[_BatchArtifact] = []
    xml_infos: list[zipfile.ZipInfo] = []
    xml_total_size = 0

    try:
        if isinstance(zip_input, bytes):
            zip_handle = zipfile.ZipFile(BytesIO(zip_input))
        else:
            zip_handle = zipfile.ZipFile(zip_input)
    except (OSError, zipfile.BadZipFile) as exc:
        raise BatchConversionError(f"Cannot read ZIP file: {exc}") from exc

    with zip_handle as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if not info.filename.lower().endswith(".xml"):
                continue
            xml_total_size += max(0, info.file_size)
            if not _safe_zip_path(info.filename):
                artifacts.append(
                    _file_error(
                        original_filename=info.filename,
                        error_type="UnsafeZipPath",
                        error_message="ZIP entry path is unsafe and was not read.",
                    )
                )
                continue
            xml_infos.append(info)

        xml_files_found = len(xml_infos) + len(artifacts)
        if xml_files_found == 0:
            raise BatchConversionError("No XML files found in ZIP.")
        if xml_files_found > active_limits.max_files:
            raise BatchConversionError(
                f"ZIP contains {xml_files_found} XML files; "
                f"max_files is {active_limits.max_files}."
            )
        if xml_total_size > active_limits.max_total_uncompressed_size:
            raise BatchConversionError(
                "ZIP XML payload exceeds max_total_uncompressed_size: "
                f"{xml_total_size} > {active_limits.max_total_uncompressed_size}."
            )

        used_output_names: set[str] = set()
        for info in xml_infos:
            if info.file_size > active_limits.max_uncompressed_file_size:
                artifacts.append(
                    _file_error(
                        original_filename=info.filename,
                        error_type="FileTooLarge",
                        error_message=(
                            "Uncompressed XML file size exceeds limit: "
                            f"{info.file_size} > "
                            f"{active_limits.max_uncompressed_file_size}."
                        ),
                    )
                )
                continue
            try:
                xml_bytes = archive.read(info)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                artifacts.append(
                    _file_error(
                        original_filename=info.filename,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )
                continue

            artifacts.append(
                _convert_xml_entry(
                    original_filename=info.filename,
                    xml_bytes=xml_bytes,
                    mapping_path=mapping_path,
                    used_output_names=used_output_names,
                )
            )

    files = [artifact.result for artifact in artifacts]
    summary = _build_summary(files=files, limits=active_limits)
    summary_json = json.dumps(summary, indent=2, ensure_ascii=False).encode("utf-8")
    summary_xlsx = _summary_xlsx_bytes(summary["files"])
    export_zip = _build_export_zip(artifacts, summary_json, summary_xlsx)
    output_paths = (
        _write_outputs(
            output_dir,
            summary_json=summary_json,
            summary_xlsx=summary_xlsx,
            export_zip=export_zip,
        )
        if output_dir is not None
        else {}
    )
    return BatchConversionReport(
        files=files,
        summary=summary,
        summary_json_bytes=summary_json,
        summary_xlsx_bytes=summary_xlsx,
        export_zip_bytes=export_zip,
        output_paths=output_paths,
    )
