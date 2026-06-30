"""Product Passport Bridge — source inventory and schema validation.

Prototype/reference only. v0.12.0 performs source inventory and structural
schema validation only. It does not claim official GS1 validation or
production compliance.

All functions are deterministic and offline. No network access is performed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

_INVENTORY_VERSION = "v0.12.0"
_PROTOTYPE_NOTE = (
    "Product Passport Bridge is a prototype/reference workflow. "
    "v0.12.0 performs source inventory and structural schema validation only. "
    "It does not claim official GS1 validation or production compliance."
)
_SCHEMA_VALIDATOR_WARNING = (
    "Structural validation only. Not official GS1 validation. "
    "Not production compliance."
)

VALID_SOURCE_TYPES = frozenset(
    {"context", "json_schema", "shacl_shape", "example", "epcis_example"}
)
VALID_SECTORS = frozenset(
    {"core", "general_product", "battery", "textile", "epcis"}
)
REQUIRED_SOURCE_FIELDS = frozenset(
    {"source_id", "title", "source_url", "source_type", "sector", "local_path"}
)


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------


def load_product_passport_source_manifest(path: str) -> dict:
    """Load the Product Passport source manifest JSON from *path*.

    Returns the parsed manifest dict.
    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    manifest_path = Path(path)
    raw = manifest_path.read_text(encoding="utf-8")
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Manifest validation
# ---------------------------------------------------------------------------


def validate_product_passport_source_manifest(
    manifest: dict,
    schema: dict | None = None,
) -> list[str]:
    """Validate *manifest* structure and return a list of error strings.

    An empty list means no errors were found.
    Does not raise — errors are returned as strings.

    Custom domain checks (required fields, duplicate ids, enum membership)
    always run. If *schema* is provided, the manifest is additionally validated
    against it with jsonschema (Draft7) when available, enforcing schema-only
    rules such as the ``source_id`` pattern and ``additionalProperties: false``.
    """
    errors: list[str] = []
    if not isinstance(manifest, dict):
        errors.append("Manifest must be a JSON object.")
        return errors

    if "sources" not in manifest:
        errors.append("Manifest is missing required field 'sources'.")
        return errors

    sources = manifest["sources"]
    if not isinstance(sources, list):
        errors.append("Field 'sources' must be a JSON array.")
        return errors

    seen_ids: set[str] = set()
    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"Source at index {idx} is not a JSON object.")
            continue

        source_id = source.get("source_id", f"<index {idx}>")

        for field in REQUIRED_SOURCE_FIELDS:
            if field not in source:
                errors.append(
                    f"Source '{source_id}' is missing required field '{field}'."
                )

        if source_id in seen_ids:
            errors.append(f"Duplicate source_id: '{source_id}'.")
        else:
            seen_ids.add(str(source_id))

        source_type = source.get("source_type")
        if source_type and source_type not in VALID_SOURCE_TYPES:
            errors.append(
                f"Source '{source_id}' has unknown source_type '{source_type}'. "
                f"Expected one of: {sorted(VALID_SOURCE_TYPES)}."
            )

        sector = source.get("sector")
        if sector and sector not in VALID_SECTORS:
            errors.append(
                f"Source '{source_id}' has unknown sector '{sector}'. "
                f"Expected one of: {sorted(VALID_SECTORS)}."
            )

    if schema is not None:
        errors.extend(_validate_manifest_against_schema(manifest, schema))

    return errors


def _validate_manifest_against_schema(manifest: dict, schema: dict) -> list[str]:
    """Validate *manifest* against *schema* using jsonschema Draft7.

    Returns a list of human-readable error strings. If jsonschema is not
    installed, returns a single note explaining the manifest schema is being
    treated as descriptive only.
    """
    try:
        from jsonschema import Draft7Validator, SchemaError
    except ImportError:
        return [
            "jsonschema is not installed: manifest schema enforcement was "
            "skipped (manifest schema treated as descriptive only)."
        ]

    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"Manifest schema is invalid: {exc.message}"]

    out: list[str] = []
    for err in sorted(Draft7Validator(schema).iter_errors(manifest), key=str):
        loc = ".".join(str(p) for p in err.path) or "root"
        out.append(f"[schema:{loc}] {err.message}")
    return out


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------


def sha256_file(path: str) -> str:
    """Compute SHA-256 hex digest of the file at *path*.

    Raises FileNotFoundError if the file does not exist.
    """
    file_path = Path(path)
    hasher = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Inventory builder
# ---------------------------------------------------------------------------


def build_product_passport_source_inventory(
    manifest: dict,
    base_dir: str = ".",
) -> dict:
    """Build a source inventory dict from *manifest*.

    *base_dir* is prepended to relative local_path values.

    Returns a dict with:
    - total_sources
    - sources_by_type
    - sources_by_sector
    - missing_local_files (list of source_ids)
    - checksum_status (list of dicts)
    - entries (list of enriched source entries)
    - inventory_version
    - prototype_note
    """
    base = Path(base_dir)
    sources: list[dict] = manifest.get("sources", [])

    sources_by_type: dict[str, int] = {}
    sources_by_sector: dict[str, int] = {}
    missing_local_files: list[str] = []
    checksum_status: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []

    for source in sources:
        source_id = str(source.get("source_id", ""))
        source_type = str(source.get("source_type", "unknown"))
        sector = str(source.get("sector", "unknown"))
        local_path_raw = source.get("local_path", "")
        expected_sha = source.get("sha256", "")

        sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1
        sources_by_sector[sector] = sources_by_sector.get(sector, 0) + 1

        # Resolve local path.
        local_path = base / local_path_raw if local_path_raw else None
        file_exists = local_path is not None and local_path.is_file()

        if not file_exists:
            missing_local_files.append(source_id)
            status = "missing"
            actual_sha = None
        elif expected_sha in (None, "", "PLACEHOLDER_SHA256_AFTER_DOWNLOAD"):
            status = "placeholder"
            try:
                actual_sha = sha256_file(str(local_path))
            except OSError:
                actual_sha = None
        else:
            try:
                actual_sha = sha256_file(str(local_path))
                status = "ok" if actual_sha == expected_sha else "mismatch"
            except OSError:
                actual_sha = None
                status = "not_computed"

        checksum_status.append(
            {
                "source_id": source_id,
                "status": status,
                "expected_sha256": expected_sha or None,
                "actual_sha256": actual_sha,
                "local_path": str(local_path_raw),
            }
        )

        entry = dict(source)
        entry["_file_exists"] = file_exists
        entry["_checksum_status"] = status
        entry["_actual_sha256"] = actual_sha
        entries.append(entry)

    return {
        "total_sources": len(sources),
        "sources_by_type": sources_by_type,
        "sources_by_sector": sources_by_sector,
        "missing_local_files": missing_local_files,
        "checksum_status": checksum_status,
        "entries": entries,
        "inventory_version": _INVENTORY_VERSION,
        "prototype_note": _PROTOTYPE_NOTE,
    }


# ---------------------------------------------------------------------------
# Report serialization
# ---------------------------------------------------------------------------


def inventory_report_bytes_json(inventory: dict) -> bytes:
    """Serialize *inventory* to UTF-8 JSON bytes."""
    return json.dumps(inventory, indent=2, ensure_ascii=False).encode("utf-8")


def inventory_report_bytes_csv(inventory: dict) -> bytes:
    """Serialize *inventory* entries to UTF-8 CSV bytes."""
    entries = inventory.get("entries", [])
    if not entries:
        return b"source_id,title,source_type,sector,version,local_path,_file_exists,_checksum_status\r\n"

    columns = [
        "source_id",
        "title",
        "source_type",
        "sector",
        "version",
        "local_path",
        "_file_exists",
        "_checksum_status",
        "_actual_sha256",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for entry in entries:
        row = {col: _csv_safe(entry.get(col, "")) for col in columns}
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def _csv_safe(value: Any) -> Any:
    """Neutralize spreadsheet formula injection for CSV cells.

    String values beginning with ``=``, ``+``, ``-``, or ``@`` are prefixed
    with a single quote so spreadsheet software does not evaluate them as
    formulas. Only affects CSV output; JSON output is unchanged.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def write_product_passport_inventory_reports(
    inventory: dict,
    output_dir: str,
) -> dict[str, str]:
    """Write inventory reports to *output_dir*.

    Creates:
    - product_passport_source_inventory.json
    - product_passport_source_inventory.csv
    - product_passport_source_summary.json

    Returns a dict mapping report key to file path string.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary = {
        "inventory_version": inventory.get("inventory_version"),
        "total_sources": inventory.get("total_sources"),
        "sources_by_type": inventory.get("sources_by_type"),
        "sources_by_sector": inventory.get("sources_by_sector"),
        "missing_local_files": inventory.get("missing_local_files"),
        "checksum_ok_count": sum(
            1
            for c in inventory.get("checksum_status", [])
            if c.get("status") == "ok"
        ),
        "checksum_placeholder_count": sum(
            1
            for c in inventory.get("checksum_status", [])
            if c.get("status") == "placeholder"
        ),
        "prototype_note": inventory.get("prototype_note"),
    }

    json_path = out / "product_passport_source_inventory.json"
    csv_path = out / "product_passport_source_inventory.csv"
    summary_path = out / "product_passport_source_summary.json"

    json_path.write_bytes(inventory_report_bytes_json(inventory))
    csv_path.write_bytes(inventory_report_bytes_csv(inventory))
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "inventory_json": str(json_path),
        "inventory_csv": str(csv_path),
        "summary_json": str(summary_path),
    }


# ---------------------------------------------------------------------------
# JSON Schema loading and validation
# ---------------------------------------------------------------------------


def load_json_schema(path: str) -> dict:
    """Load a JSON Schema from *path*.

    Returns the parsed schema dict.
    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    schema_path = Path(path)
    raw = schema_path.read_text(encoding="utf-8")
    return json.loads(raw)


def load_product_passport_json(path: str) -> dict:
    """Load a Product Passport JSON file from *path*.

    Returns the parsed dict.
    Raises FileNotFoundError or json.JSONDecodeError on failure.
    """
    pp_path = Path(path)
    raw = pp_path.read_text(encoding="utf-8")
    return json.loads(raw)


def validate_product_passport_json(instance: dict, schema: dict) -> dict:
    """Validate *instance* against *schema*.

    Tries to use jsonschema (Draft7Validator) if available.
    Falls back to a minimal structural check (required fields only) otherwise.

    Returns a report dict with:
    - validation_status: "valid" | "invalid" | "schema_error" | "not_run"
    - errors: list of error strings
    - warnings: list of warning strings
    - validator_version: str
    - prototype_warning
    """
    errors: list[str] = []
    warnings: list[str] = []
    validator_version = "unknown"
    validator_mode = "minimal_fallback"

    try:
        import jsonschema
        from jsonschema import Draft7Validator, SchemaError, ValidationError

        validator_mode = "jsonschema"

        try:
            import importlib.metadata as _imeta
            validator_version = "jsonschema " + _imeta.version("jsonschema")
        except Exception:
            validator_version = "jsonschema (version unknown)"

        # Check the schema itself first.
        try:
            Draft7Validator.check_schema(schema)
        except SchemaError as exc:
            return {
                "validation_status": "schema_error",
                "errors": [f"Schema is invalid: {exc.message}"],
                "warnings": [],
                "validator_version": validator_version,
                "validator_mode": validator_mode,
                "prototype_warning": _SCHEMA_VALIDATOR_WARNING,
            }

        validator = Draft7Validator(schema)
        for error in sorted(validator.iter_errors(instance), key=str):
            errors.append(
                f"[{'.'.join(str(p) for p in error.path) or 'root'}] {error.message}"
            )

        validation_status = "valid" if not errors else "invalid"

    except ImportError:
        # Minimal structural fallback: check required fields only.
        validator_version = "minimal_fallback (jsonschema not installed)"
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in instance:
                errors.append(
                    f"Required field '{field}' is missing (minimal fallback check)."
                )
        warnings.append(
            "FALLBACK MODE: jsonschema is not installed, so only required-field "
            "presence was checked — this is weaker than full Draft7 validation. "
            "A 'valid' result here does not mean the document passed structural "
            "schema validation. Install jsonschema for full Draft7 validation."
        )
        validation_status = "valid" if not errors else "invalid"

    return {
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
        "validator_version": validator_version,
        "validator_mode": validator_mode,
        "prototype_warning": _SCHEMA_VALIDATOR_WARNING,
    }


def _find_manifest_entry(
    manifest: dict | None,
    schema_path: str,
) -> dict | None:
    """Return the manifest source entry whose local_path matches *schema_path*, or None."""
    if not manifest:
        return None
    schema_path_str = str(Path(schema_path).as_posix())
    for source in manifest.get("sources", []):
        local = source.get("local_path", "")
        if local and str(Path(local).as_posix()) in (
            schema_path_str,
            # Also check just the filename in case relative paths differ.
            Path(schema_path_str).name,
        ):
            return source
    return None


def validate_product_passport_file(
    instance_path: str,
    schema_path: str,
    manifest: dict | None = None,
) -> dict:
    """Load and validate *instance_path* against *schema_path*.

    Returns a full validation report dict with:
    - validation_status
    - schema_id
    - schema_title
    - instance_file
    - schema_file
    - errors
    - warnings
    - validator_version
    - source_manifest_entry
    - prototype_warning
    """
    try:
        instance = load_product_passport_json(instance_path)
    except FileNotFoundError:
        return {
            "validation_status": "schema_error",
            "schema_id": None,
            "schema_title": None,
            "instance_file": instance_path,
            "schema_file": schema_path,
            "errors": [f"Instance file not found: {instance_path}"],
            "warnings": [],
            "validator_version": "none",
            "source_manifest_entry": None,
            "prototype_warning": _SCHEMA_VALIDATOR_WARNING,
        }
    except json.JSONDecodeError as exc:
        return {
            "validation_status": "schema_error",
            "schema_id": None,
            "schema_title": None,
            "instance_file": instance_path,
            "schema_file": schema_path,
            "errors": [f"Instance file is not valid JSON: {exc}"],
            "warnings": [],
            "validator_version": "none",
            "source_manifest_entry": None,
            "prototype_warning": _SCHEMA_VALIDATOR_WARNING,
        }

    try:
        schema = load_json_schema(schema_path)
    except FileNotFoundError:
        return {
            "validation_status": "schema_error",
            "schema_id": None,
            "schema_title": None,
            "instance_file": instance_path,
            "schema_file": schema_path,
            "errors": [f"Schema file not found: {schema_path}"],
            "warnings": [],
            "validator_version": "none",
            "source_manifest_entry": None,
            "prototype_warning": _SCHEMA_VALIDATOR_WARNING,
        }
    except json.JSONDecodeError as exc:
        return {
            "validation_status": "schema_error",
            "schema_id": None,
            "schema_title": None,
            "instance_file": instance_path,
            "schema_file": schema_path,
            "errors": [f"Schema file is not valid JSON: {exc}"],
            "warnings": [],
            "validator_version": "none",
            "source_manifest_entry": None,
            "prototype_warning": _SCHEMA_VALIDATOR_WARNING,
        }

    schema_id = schema.get("$id") or schema.get("id")
    schema_title = schema.get("title")

    manifest_entry = _find_manifest_entry(manifest, schema_path)

    result = validate_product_passport_json(instance, schema)
    result.update(
        {
            "schema_id": schema_id,
            "schema_title": schema_title,
            "instance_file": instance_path,
            "schema_file": schema_path,
            "source_manifest_entry": manifest_entry,
        }
    )
    return result


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------


def write_schema_validation_report(report: dict, output_dir: str) -> str:
    """Write *report* to *output_dir* as product_passport_validation_report.json.

    Returns the path string.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "product_passport_validation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(report_path)
