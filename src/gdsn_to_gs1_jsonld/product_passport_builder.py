"""Product Passport Builder — minimal-schema prototype mode (v0.13.0).

Wraps GS1 Web Vocabulary JSON-LD (from the converter, the Manual JSON-LD
Prototype Builder, or pasted/uploaded input) into a prototype Product Passport
JSON-LD envelope, and validates the built envelope against a local structural
schema (the committed built-in minimal schema by default).

Prototype/reference only. Structural schema validation only. This is NOT
official GS1 validation, NOT EU DPP regulatory compliance, and NOT
production-ready. No online fetching is performed. Reuses the v0.12.x validator
in ``product_passport_sources`` — validation logic is not duplicated here.

All functions are deterministic and offline. ``generatedAt`` is omitted unless
explicitly supplied via options, so default output is byte-stable for tests.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .jsonld_builder import GS1_WEBVOC_CONTEXT
from .product_passport_sources import (
    load_json_schema,
    validate_product_passport_json,
)

BUILDER_VERSION = "v0.13.0"
VALIDATION_MODE = "minimal-schema-prototype"
PASSPORT_TYPE_DEFAULT = "product-passport-prototype"
PASSPORT_VERSION_DEFAULT = "v0.13.0-prototype"
STATUS_DEFAULT = "prototype"
DEFAULT_SCHEMA_PATH = (
    "product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json"
)

PROTOTYPE_NOTICE = (
    "Prototype/reference Product Passport JSON-LD generated for standards "
    "discussion only. Structural schema validation only. Not official GS1 "
    "validation, not EU DPP regulatory compliance, and not production-ready."
)


# ---------------------------------------------------------------------------
# Input loading / normalization
# ---------------------------------------------------------------------------


def normalize_gs1_jsonld_input(data: Any) -> dict:
    """Coerce *data* into a GS1 JSON-LD object.

    Accepts a dict (returned as-is) or a JSON string/bytes (parsed).
    Raises ValueError if the input is not a JSON object.
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Input is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("GS1 JSON-LD input must be a JSON object.")
        return parsed
    raise ValueError("GS1 JSON-LD input must be a dict or JSON string.")


def load_gs1_jsonld(path_or_text: str) -> dict:
    """Load GS1 JSON-LD from a file path or a JSON text string.

    If *path_or_text* names an existing file, it is read; otherwise the string
    is parsed as JSON text. Raises ValueError on invalid JSON.
    """
    candidate = Path(path_or_text)
    try:
        is_file = candidate.is_file()
    except OSError:
        is_file = False
    if is_file:
        return normalize_gs1_jsonld_input(candidate.read_text(encoding="utf-8"))
    return normalize_gs1_jsonld_input(path_or_text)


# ---------------------------------------------------------------------------
# Extraction helpers (tolerant of converter and manual-builder output shapes)
# ---------------------------------------------------------------------------


def extract_language_values(value: Any) -> list[dict[str, str]]:
    """Normalize a possibly language-tagged value into a list of dicts.

    Accepts a string, a ``{"@value": ..., "@language": ...}`` object, or a list
    of either. Returns a list of ``{"@value": str[, "@language": str]}``.
    """
    out: list[dict[str, str]] = []
    if value is None:
        return out
    items = value if isinstance(value, list) else [value]
    for item in items:
        if isinstance(item, dict):
            val = item.get("@value", item.get("value"))
            lang = item.get("@language", item.get("language"))
            if val is not None and str(val).strip():
                entry = {"@value": str(val)}
                if lang:
                    entry["@language"] = str(lang)
                out.append(entry)
        elif isinstance(item, str) and item.strip():
            out.append({"@value": item})
    return out


def _first_value(gs1_jsonld: dict, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if key in gs1_jsonld:
            values = extract_language_values(gs1_jsonld[key])
            if values:
                return values[0]["@value"]
    return None


def extract_product_identifier(gs1_jsonld: dict) -> str | None:
    """Return the JSON-LD node identifier (@id/id), or None."""
    identifier = gs1_jsonld.get("@id", gs1_jsonld.get("id"))
    return str(identifier) if identifier else None


def extract_gtin(gs1_jsonld: dict) -> str | None:
    """Extract a GTIN from a direct field or from a GS1 Digital Link @id."""
    for key in ("gtin", "gs1:gtin"):
        raw = gs1_jsonld.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        if isinstance(raw, dict) and raw.get("@value"):
            return str(raw["@value"]).strip()
    identifier = extract_product_identifier(gs1_jsonld)
    if identifier:
        match = re.search(r"/01/(\d{8,14})", identifier)
        if match:
            return match.group(1)
    return None


def extract_product_name(gs1_jsonld: dict) -> str | None:
    """Extract a display product name, tolerant of language-value shapes."""
    return _first_value(
        gs1_jsonld, ("productName", "gs1:productName", "name", "schema:name")
    )


def extract_product_description(gs1_jsonld: dict) -> str | None:
    """Extract a display product description."""
    return _first_value(
        gs1_jsonld,
        (
            "productDescription",
            "gs1:productDescription",
            "description",
            "schema:description",
        ),
    )


def extract_brand(gs1_jsonld: dict) -> str | None:
    """Extract a brand string, tolerant of nested brand objects."""
    for key in ("brand", "brandName", "gs1:brand", "gs1:brandName", "schema:brand"):
        raw = gs1_jsonld.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        if isinstance(raw, dict):
            values = extract_language_values(raw.get("name", raw))
            if values:
                return values[0]["@value"]
        values = extract_language_values(raw)
        if values:
            return values[0]["@value"]
    return None


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


def _default_passport_id(gtin: str | None) -> str:
    suffix = gtin if gtin else "unidentified"
    return f"urn:gdsn-gs1-jsonld:product-passport:{suffix}"


def _resolve_options(options: dict | None) -> dict:
    opts = dict(options or {})
    schema_path = opts.get("validation_schema") or DEFAULT_SCHEMA_PATH
    return {
        "passport_id": opts.get("passport_id"),
        "passport_type": opts.get("passport_type", PASSPORT_TYPE_DEFAULT),
        "passport_version": opts.get("passport_version", PASSPORT_VERSION_DEFAULT),
        "status": opts.get("status", STATUS_DEFAULT),
        "default_language": opts.get("default_language", "en"),
        "include_source_gs1_jsonld": opts.get("include_source_gs1_jsonld", True),
        "validation_schema": schema_path,
        "schema_name": Path(schema_path).name,
        "validation_required_before_download": opts.get(
            "validation_required_before_download", False
        ),
        "prototype_notice": opts.get("prototype_notice", PROTOTYPE_NOTICE),
        "generated_at": opts.get("generated_at"),
    }


# ---------------------------------------------------------------------------
# Envelope builder
# ---------------------------------------------------------------------------


def build_minimal_product_passport(
    gs1_jsonld: dict,
    options: dict | None = None,
) -> dict:
    """Build a prototype Product Passport JSON-LD envelope from GS1 JSON-LD.

    Deterministic by default (``generatedAt`` omitted unless supplied). The
    envelope always carries ``@context`` and ``@type`` so it satisfies the
    built-in minimal structural schema.
    """
    gs1_jsonld = normalize_gs1_jsonld_input(gs1_jsonld)
    opts = _resolve_options(options)

    gtin = extract_gtin(gs1_jsonld)
    product_name = extract_product_name(gs1_jsonld)
    passport_id = opts["passport_id"] or _default_passport_id(gtin)
    identifier = extract_product_identifier(gs1_jsonld) or (
        f"https://id.gs1.org/01/{gtin}" if gtin else None
    )

    envelope: dict[str, Any] = {
        "@context": GS1_WEBVOC_CONTEXT,
        "@type": "Product",
    }
    if identifier:
        envelope["@id"] = identifier
    envelope.update(
        {
            "productPassportId": passport_id,
            "passportType": opts["passport_type"],
            "passportVersion": opts["passport_version"],
            "status": opts["status"],
            "prototypeNotice": opts["prototype_notice"],
            "defaultLanguage": opts["default_language"],
            "source": {
                "sourceType": "gs1-web-vocabulary-jsonld",
                "sourceFormat": "json-ld",
                "sourceGtin": gtin,
                "sourceProductName": product_name,
            },
            "validation": {
                "validationMode": VALIDATION_MODE,
                "schema": opts["schema_name"],
                "note": (
                    "Structural validation result is provided separately in the "
                    "validation report. Passing means only that the JSON matches "
                    "the selected local structural schema."
                ),
            },
            "createdByVersion": BUILDER_VERSION,
        }
    )
    if opts["generated_at"]:
        envelope["generatedAt"] = opts["generated_at"]
    if opts["include_source_gs1_jsonld"]:
        envelope["product"] = gs1_jsonld
    return envelope


def build_product_passport_envelope(
    gs1_jsonld: dict,
    options: dict | None = None,
) -> dict:
    """Alias for :func:`build_minimal_product_passport` (v0.13.0 mode)."""
    return build_minimal_product_passport(gs1_jsonld, options)


# ---------------------------------------------------------------------------
# Validation (reuses product_passport_sources — no duplicate logic)
# ---------------------------------------------------------------------------


def validate_built_product_passport(
    product_passport: dict,
    schema_path: str = DEFAULT_SCHEMA_PATH,
) -> dict:
    """Validate a built Product Passport against a local structural schema.

    Reuses ``product_passport_sources.validate_product_passport_json``. Returns
    the validation report dict, enriched with the schema file path. A schema
    that cannot be read yields a ``schema_error`` report rather than raising.
    """
    try:
        schema = load_json_schema(schema_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        return {
            "validation_status": "schema_error",
            "errors": [f"Schema could not be loaded: {exc}"],
            "warnings": [],
            "validator_version": "none",
            "validator_mode": "none",
            "schema_file": schema_path,
            "prototype_warning": PROTOTYPE_NOTICE,
        }
    report = validate_product_passport_json(product_passport, schema)
    report["schema_file"] = schema_path
    report["instance"] = "product_passport_prototype"
    report["prototype_warning"] = PROTOTYPE_NOTICE
    return report


# ---------------------------------------------------------------------------
# Serialization / summary / output
# ---------------------------------------------------------------------------


def product_passport_to_json_bytes(product_passport: dict) -> bytes:
    """Deterministic UTF-8 JSON-LD bytes for the built Product Passport."""
    return (
        json.dumps(product_passport, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def product_passport_report_bytes_json(report: dict) -> bytes:
    """Deterministic UTF-8 JSON bytes for a validation report."""
    return (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build_product_passport_summary(
    product_passport: dict,
    validation_report: dict,
) -> dict:
    """Combine passport metadata and validation outcome into a summary dict."""
    source = product_passport.get("source", {})
    return {
        "productPassportId": product_passport.get("productPassportId"),
        "passportType": product_passport.get("passportType"),
        "passportVersion": product_passport.get("passportVersion"),
        "status": product_passport.get("status"),
        "sourceGtin": source.get("sourceGtin"),
        "sourceProductName": source.get("sourceProductName"),
        "validationMode": VALIDATION_MODE,
        "schema": product_passport.get("validation", {}).get("schema"),
        "structuralValidationStatus": validation_report.get("validation_status"),
        "validatorMode": validation_report.get("validator_mode"),
        "errorCount": len(validation_report.get("errors", [])),
        "prototypeNotice": product_passport.get("prototypeNotice", PROTOTYPE_NOTICE),
        "builderVersion": BUILDER_VERSION,
    }


def write_product_passport_outputs(
    product_passport: dict,
    validation_report: dict,
    output_dir: str,
) -> dict[str, str]:
    """Write the passport, validation report, and summary to *output_dir*.

    Creates:
    - product_passport.jsonld
    - product_passport_validation_report.json
    - product_passport_summary.json

    Returns a dict mapping output key to file path string.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    passport_path = out / "product_passport.jsonld"
    report_path = out / "product_passport_validation_report.json"
    summary_path = out / "product_passport_summary.json"

    passport_path.write_bytes(product_passport_to_json_bytes(product_passport))
    report_path.write_bytes(product_passport_report_bytes_json(validation_report))
    summary = build_product_passport_summary(product_passport, validation_report)
    summary_path.write_bytes(
        (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    )

    return {
        "product_passport_jsonld": str(passport_path),
        "validation_report_json": str(report_path),
        "summary_json": str(summary_path),
    }
