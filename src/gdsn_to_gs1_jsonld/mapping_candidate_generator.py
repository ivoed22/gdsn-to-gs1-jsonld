"""Mapping candidate generator for GDSN-to-GS1-WebVoc review support.

This module proposes candidate GDSN/BMS/XPath source fields for GS1 Web
Vocabulary properties.  All generation is deterministic and offline.  No
mappings are automatically accepted or written.

Review-only scope
-----------------
Candidates are review support only.  They do not update mapping YAML or
converter behavior.  The caller must review each candidate before any mapping
decision is made.

Created-by version
------------------
All generated candidates carry ``created_by_version = "v0.11.0"``.
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CREATED_BY_VERSION = "v0.11.0"

# Reason codes used in candidate scoring.
REASON_CODES = {
    "existing_mapping_catalog_match": "Property already appears in mapping catalog as mapped.",
    "mapping_yaml_canonical_field_match": "GDSN attribute referenced in active YAML for this property.",
    "semantic_resource_urn_match": "GDSN SemanticResourceURN matches WebVoc term URI.",
    "exact_property_name_match": "WebVoc label or compact name exactly matches GDSN attribute name.",
    "label_attribute_token_overlap": "Shared tokens between WebVoc label/comment and GDSN attribute name/definition.",
    "xpath_terminal_match": "XPath terminal segment resembles WebVoc compact name tokens.",
    "definition_comment_overlap": "Shared tokens between WebVoc comment and GDSN definition.",
    "range_datatype_compatible": "WebVoc range and GDSN DataType appear compatible.",
    "quantity_uom_compatible": "Quantity-like property paired with UOM-enabled GDSN attribute.",
    "code_list_signal": "Both property and attribute involve controlled value lists.",
    "standards_review_linked": "Property is referenced in an open standards-review backlog entry.",
    "deleted_attribute_warning": "GDSN attribute is marked deleted (is_deleted=true).",
    "datatype_mismatch_warning": "WebVoc range and GDSN DataType appear incompatible.",
    "class_row_not_attribute": "Row represents a Class or Module, not a leaf Attribute.",
}

# Score weights per signal (positive) and penalties (negative).
_SIGNAL_WEIGHTS: dict[str, float] = {
    "existing_mapping_catalog_match": 0.90,
    "mapping_yaml_canonical_field_match": 0.65,
    "semantic_resource_urn_match": 0.80,
    "exact_property_name_match": 0.70,
    "label_attribute_token_overlap": 0.35,
    "xpath_terminal_match": 0.25,
    "definition_comment_overlap": 0.20,
    "range_datatype_compatible": 0.15,
    "quantity_uom_compatible": 0.20,
    "code_list_signal": 0.15,
    "standards_review_linked": 0.10,
}

_PENALTY_WEIGHTS: dict[str, float] = {
    "deleted_attribute_warning": -0.30,
    "datatype_mismatch_warning": -0.15,
    "class_row_not_attribute": -0.20,
}

# Confidence thresholds.
CONFIDENCE_HIGH = 0.70
CONFIDENCE_MEDIUM = 0.40
CONFIDENCE_LOW = 0.15

# Compatible range/datatype mappings.
_RANGE_DATATYPE_COMPAT: dict[str, set[str]] = {
    "xsd:string": {"string", "description200", "description40", "string40", "string80",
                   "string200", "string500", "string5000", "formatteddescription5000",
                   "partneridentification", "gln", "gtin", "string1..80", "alphanumerictext5000"},
    "rdf:langstring": {"string", "description200", "description40", "formatteddescription5000",
                       "languagespecificstring40", "languagespecificstring200",
                       "languagespecificstring5000", "description"},
    "xsd:boolean": {"boolean"},
    "xsd:decimal": {"decimal", "measurement", "numeric"},
    "xsd:integer": {"integer", "count"},
    "xsd:float": {"float", "decimal", "measurement"},
    "xsd:double": {"float", "decimal", "double"},
    "xsd:date": {"date", "datetime"},
    "xsd:datetime": {"datetime", "date"},
    "xsd:anyuri": {"string", "anyuri", "url"},
    "gs1:quantitativevalue": {"measurement", "decimal", "float"},
}

_RANGE_DATATYPE_INCOMPAT: dict[str, set[str]] = {
    "xsd:boolean": {"string", "description200", "description40", "measurement",
                    "decimal", "gtin", "gln"},
    "xsd:integer": {"boolean", "string"},
    "xsd:date": {"boolean", "string", "gtin"},
    "rdf:langstring": {"boolean", "integer", "decimal"},
}

# Words to exclude from token matching (stopwords).
_STOPWORDS = frozenset({
    "a", "an", "the", "of", "in", "for", "to", "and", "or", "is", "are",
    "be", "with", "that", "this", "as", "at", "by", "has", "have", "it",
    "its", "not", "on", "from", "which", "when", "where", "type", "code",
    "value", "number", "name", "data", "item", "product", "gdsn", "gs1",
    "urn", "gdd", "bie",
})


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_gdsn_reference(path: str) -> list[dict]:
    """Load GDSN normalized reference CSV and return list of row dicts."""
    result: list[dict] = []
    p = Path(path)
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            result.append(dict(row))
    return result


def load_webvoc_properties(path: str) -> list[dict]:
    """Load WebVoc properties normalized CSV and return list of row dicts."""
    result: list[dict] = []
    p = Path(path)
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            result.append(dict(row))
    return result


def load_existing_mapping_catalog(path: str) -> list[dict]:
    """Load the mapping catalog CSV and return list of row dicts."""
    result: list[dict] = []
    p = Path(path)
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            result.append(dict(row))
    return result


def load_mapping_yaml(path: str) -> dict:
    """Load YAML mapping file and return parsed dict."""
    p = Path(path)
    with p.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_standards_backlog(path: str) -> list[dict]:
    """Load standards review backlog JSON.  Returns empty list on missing file."""
    p = Path(path)
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        return raw
    return []


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------


def _build_catalog_index(catalog_rows: list[dict]) -> dict[str, list[dict]]:
    """Index catalog rows by jsonld_property (gs1:xxx or similar).

    Only indexes by the full jsonld_property value.  Compound property paths
    like ``gs1:hasAllergen/gs1:allergenType`` are indexed as-is so that the
    first segment ``gs1:hasAllergen`` does not generate spurious matches for
    unrelated properties.
    """
    index: dict[str, list[dict]] = {}
    for row in catalog_rows:
        prop = str(row.get("jsonld_property") or "").strip()
        if prop:
            index.setdefault(prop, []).append(row)
    return index


def _build_yaml_property_field_index(mapping_yaml: dict) -> dict[str, list[str]]:
    """Build mapping from jsonld_property -> [canonical_field, ...] from YAML."""
    index: dict[str, list[str]] = {}

    def _collect_fields(fields_list: list[dict], parent_prop: str | None = None) -> None:
        for field in fields_list:
            if not isinstance(field, dict):
                continue
            prop = str(field.get("jsonld_property") or "").strip()
            canonical = str(field.get("canonical_field") or "").strip()
            if prop and canonical:
                index.setdefault(prop, []).append(canonical)
            # Also map the parent object property to child canonical fields.
            if parent_prop and canonical:
                index.setdefault(parent_prop, []).append(canonical)

    # Top-level fields.
    for f in mapping_yaml.get("fields", []):
        if isinstance(f, dict):
            prop = str(f.get("jsonld_property") or "").strip()
            canonical = str(f.get("canonical_field") or "").strip()
            if prop and canonical:
                index.setdefault(prop, []).append(canonical)

    # Object mapping fields.
    for obj in mapping_yaml.get("object_mappings", []):
        if not isinstance(obj, dict):
            continue
        parent_prop = str(obj.get("jsonld_property") or "").strip()
        child_fields = obj.get("fields") or []
        _collect_fields(child_fields, parent_prop)

    return index


def _build_yaml_bms_id_index(mapping_yaml: dict) -> dict[str, list[str]]:
    """Build mapping from bms_id -> [jsonld_property] from YAML (via id field)."""
    # YAML doesn't directly carry BMS IDs; this returns empty dict.
    return {}


def _build_backlog_property_index(backlog: list[dict]) -> dict[str, list[str]]:
    """Build mapping from jsonld_property -> [sdr_id, ...] from backlog."""
    index: dict[str, list[str]] = {}
    for entry in backlog:
        sdr_id = str(entry.get("id") or "").strip()
        for prop in entry.get("affected_properties", []):
            prop_str = str(prop).strip()
            if prop_str and sdr_id:
                index.setdefault(prop_str, []).append(sdr_id)
    return index


def build_candidate_inputs(
    webvoc_path: str,
    gdsn_path: str,
    catalog_path: str,
    mapping_path: str,
    backlog_path: str | None = None,
) -> dict:
    """Load and index all source inputs needed for candidate generation."""
    webvoc_rows = load_webvoc_properties(webvoc_path)
    gdsn_rows = load_gdsn_reference(gdsn_path)
    catalog_rows = load_existing_mapping_catalog(catalog_path)
    mapping_yaml = load_mapping_yaml(mapping_path)
    backlog = load_standards_backlog(backlog_path) if backlog_path else []

    # Build indexes.
    catalog_index = _build_catalog_index(catalog_rows)
    yaml_property_field_index = _build_yaml_property_field_index(mapping_yaml)
    backlog_property_index = _build_backlog_property_index(backlog)

    # Build GDSN attribute-name index (case-insensitive).
    gdsn_by_name: dict[str, list[dict]] = {}
    for row in gdsn_rows:
        name = str(row.get("attribute_name") or "").strip().lower()
        if name:
            gdsn_by_name.setdefault(name, []).append(row)

    # Build GDSN BMS-ID index.
    gdsn_by_bms_id: dict[str, dict] = {}
    for row in gdsn_rows:
        bms_id = str(row.get("bms_id") or "").strip()
        if bms_id:
            gdsn_by_bms_id[bms_id] = row

    return {
        "webvoc_rows": webvoc_rows,
        "gdsn_rows": gdsn_rows,
        "catalog_rows": catalog_rows,
        "mapping_yaml": mapping_yaml,
        "backlog": backlog,
        "catalog_index": catalog_index,
        "yaml_property_field_index": yaml_property_field_index,
        "backlog_property_index": backlog_property_index,
        "gdsn_by_name": gdsn_by_name,
        "gdsn_by_bms_id": gdsn_by_bms_id,
    }


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def normalize_text(value: str) -> str:
    """Normalize Unicode, remove punctuation, lowercase."""
    if not value:
        return ""
    nfkd = unicodedata.normalize("NFKD", value)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric chars with space.
    clean = re.sub(r"[^a-zA-Z0-9]+", " ", ascii_text)
    return clean.lower().strip()


def tokenize_mapping_text(value: str) -> set[str]:
    """Tokenize a normalized text value into a set of non-stopword tokens."""
    if not value:
        return set()
    normalized = normalize_text(value)
    tokens = set(normalized.split())
    # Also split camelCase into sub-tokens.
    camel_tokens: set[str] = set()
    for token in tokens:
        parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", token).lower().split()
        camel_tokens.update(parts)
    tokens.update(camel_tokens)
    return tokens - _STOPWORDS - {""}


def _compact_name_tokens(compact_name: str) -> set[str]:
    """Tokenize a compact name like acceptedPaymentMethod."""
    if not compact_name:
        return set()
    # Split camelCase.
    parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", compact_name)
    return {p.lower() for p in parts.split() if p.lower() not in _STOPWORDS and p}


def _xpath_terminal(xpath: str) -> str:
    """Extract the last path segment from an XPath expression."""
    if not xpath:
        return ""
    # Remove attributes.
    terminal = xpath.rstrip("/").split("/")[-1]
    # Remove namespace prefix and attribute marker.
    if ":" in terminal:
        terminal = terminal.split(":", 1)[-1]
    terminal = terminal.lstrip("@")
    # Remove predicates.
    terminal = re.sub(r"\[.*?\]", "", terminal)
    return terminal.strip()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_candidate(
    webvoc_property: dict,
    gdsn_attribute: dict,
    context: dict,
) -> tuple[float, list[str], list[str]]:
    """Score a (WebVoc property, GDSN attribute) pair.

    Returns
    -------
    tuple[float, list[str], list[str]]
        (score, reasons, warnings)
        score is in [0.0, 1.0] (capped).
        reasons is a list of reason codes that fired.
        warnings is a list of warning reason codes that fired.
    """
    reasons: list[str] = []
    warnings: list[str] = []
    raw_score: float = 0.0

    prop_id = str(webvoc_property.get("term_id") or "").strip()
    compact_name = str(webvoc_property.get("compact_name") or "").strip()
    prop_label = str(webvoc_property.get("label") or "").strip()
    prop_comment = str(webvoc_property.get("comment") or "").strip()
    prop_range = str(webvoc_property.get("range") or "").strip().lower()

    attr_name = str(gdsn_attribute.get("attribute_name") or "").strip()
    attr_name_lower = attr_name.lower()
    attr_definition = str(gdsn_attribute.get("definition") or "").strip()
    attr_xpath = str(gdsn_attribute.get("xpath") or "").strip()
    attr_datatype = str(gdsn_attribute.get("data_type") or "").strip()
    attr_urn = str(gdsn_attribute.get("semantic_resource_urn") or "").strip()
    attr_code_list_name = str(gdsn_attribute.get("code_list_name") or "").strip()
    attr_uom_enabled = str(gdsn_attribute.get("uom_enabled") or "").strip().lower() == "yes"
    attr_is_deleted = str(gdsn_attribute.get("is_deleted") or "false").strip().lower() == "true"
    attr_row_type = str(gdsn_attribute.get("row_type") or "").strip()

    catalog_index = context.get("catalog_index", {})
    yaml_prop_index = context.get("yaml_property_field_index", {})
    backlog_index = context.get("backlog_property_index", {})

    # --- Negative signals first ---
    if attr_is_deleted:
        warnings.append("deleted_attribute_warning")
        raw_score += _PENALTY_WEIGHTS["deleted_attribute_warning"]

    row_type_lower = attr_row_type.lower()
    if row_type_lower in {"class", "module", "root"} or (
        row_type_lower and row_type_lower not in {"attribute", ""}
    ):
        warnings.append("class_row_not_attribute")
        raw_score += _PENALTY_WEIGHTS["class_row_not_attribute"]

    # --- Positive signals ---

    # Signal 1: existing_mapping_catalog_match
    # Check only direct prop_id match in catalog (no compound-path fallback).
    catalog_hits = catalog_index.get(prop_id, [])
    if catalog_hits:
        # Only fire if this GDSN attribute's bms_id or name matches a catalog row.
        attr_bms_str = str(gdsn_attribute.get("bms_id") or "").strip()
        matched_statuses = {
            str(r.get("mapping_status") or "").lower() for r in catalog_hits
            if (
                str(r.get("gdsn_bms_id") or "").strip() == attr_bms_str
                or str(r.get("gdsn_attribute_name") or "").strip().lower() == attr_name_lower
            )
        }
        if any(
            s in {"mapped_official_bms_xpath", "candidate_official_bms_xpath",
                  "candidate", "mapped"}
            for s in matched_statuses
        ):
            reasons.append("existing_mapping_catalog_match")
            raw_score += _SIGNAL_WEIGHTS["existing_mapping_catalog_match"]

    # Signal 2: mapping_yaml_canonical_field_match
    # Only fire if the GDSN attribute name matches a canonical_field in the YAML
    # that is linked to this property.
    yaml_fields = yaml_prop_index.get(prop_id, [])
    if yaml_fields and attr_name:
        attr_name_for_yaml = attr_name_lower.replace(" ", "_")
        # Also try the attribute name as-is (canonical fields use snake_case).
        yaml_match = any(
            str(f).lower().replace(" ", "_") == attr_name_for_yaml
            or str(f).lower() == attr_name_lower
            for f in yaml_fields
        )
        if yaml_match:
            reasons.append("mapping_yaml_canonical_field_match")
            raw_score += _SIGNAL_WEIGHTS["mapping_yaml_canonical_field_match"]

    # Signal 3: semantic_resource_urn_match
    if attr_urn:
        # Normalize both sides for comparison.
        prop_local = compact_name.lower()
        urn_parts = attr_urn.lower().split(".")
        urn_last = urn_parts[-1] if urn_parts else ""
        if prop_local and (
            prop_local in attr_urn.lower()
            or urn_last == prop_local
            or normalize_text(prop_local) == normalize_text(urn_last)
        ):
            reasons.append("semantic_resource_urn_match")
            raw_score += _SIGNAL_WEIGHTS["semantic_resource_urn_match"]

    # Signal 4: exact_property_name_match
    compact_lower = compact_name.lower()
    label_lower = prop_label.lower()
    if attr_name_lower and (
        attr_name_lower == compact_lower or attr_name_lower == label_lower
    ):
        reasons.append("exact_property_name_match")
        raw_score += _SIGNAL_WEIGHTS["exact_property_name_match"]

    # Signal 5: label_attribute_token_overlap
    prop_tokens = tokenize_mapping_text(prop_label) | _compact_name_tokens(compact_name)
    attr_tokens = tokenize_mapping_text(attr_name)
    if prop_tokens and attr_tokens:
        overlap = prop_tokens & attr_tokens
        if len(overlap) >= 1:
            # Weight by fraction of overlap.
            overlap_frac = len(overlap) / max(len(prop_tokens), len(attr_tokens))
            if overlap_frac >= 0.3 or "exact_property_name_match" not in reasons:
                reasons.append("label_attribute_token_overlap")
                raw_score += _SIGNAL_WEIGHTS["label_attribute_token_overlap"] * overlap_frac

    # Signal 6: xpath_terminal_match
    terminal = _xpath_terminal(attr_xpath)
    if terminal:
        terminal_tokens = _compact_name_tokens(terminal)
        prop_name_tokens = _compact_name_tokens(compact_name)
        if terminal_tokens and prop_name_tokens:
            overlap = terminal_tokens & prop_name_tokens
            if overlap:
                reasons.append("xpath_terminal_match")
                raw_score += _SIGNAL_WEIGHTS["xpath_terminal_match"]

    # Signal 7: definition_comment_overlap
    if attr_definition and prop_comment:
        def_tokens = tokenize_mapping_text(attr_definition)
        comment_tokens = tokenize_mapping_text(prop_comment)
        if def_tokens and comment_tokens:
            overlap = def_tokens & comment_tokens
            if len(overlap) >= 2:
                overlap_frac = len(overlap) / max(len(def_tokens), len(comment_tokens))
                reasons.append("definition_comment_overlap")
                raw_score += _SIGNAL_WEIGHTS["definition_comment_overlap"] * overlap_frac

    # Signal 8: range_datatype_compatible
    if attr_datatype and prop_range:
        datatype_lower = attr_datatype.lower().strip()
        compatible = _RANGE_DATATYPE_COMPAT.get(prop_range, set())
        incompatible = _RANGE_DATATYPE_INCOMPAT.get(prop_range, set())
        if datatype_lower in compatible:
            reasons.append("range_datatype_compatible")
            raw_score += _SIGNAL_WEIGHTS["range_datatype_compatible"]
        elif datatype_lower in incompatible:
            warnings.append("datatype_mismatch_warning")
            raw_score += _PENALTY_WEIGHTS["datatype_mismatch_warning"]

    # Signal 9: quantity_uom_compatible
    is_quantity_prop = prop_range in {
        "gs1:quantitativevalue", "gs1:measurementtype", "gs1:measurement"
    } or "quantity" in compact_lower or "measurement" in compact_lower or "content" in compact_lower
    if is_quantity_prop and attr_uom_enabled:
        reasons.append("quantity_uom_compatible")
        raw_score += _SIGNAL_WEIGHTS["quantity_uom_compatible"]

    # Signal 10: code_list_signal
    has_code_list_prop = any(
        word in prop_range.lower()
        for word in {"code", "enumeration", "type"}
    ) or any(
        word in compact_lower
        for word in {"code", "type", "status", "method"}
    )
    has_code_list_attr = bool(attr_code_list_name.strip())
    if has_code_list_prop and has_code_list_attr:
        reasons.append("code_list_signal")
        raw_score += _SIGNAL_WEIGHTS["code_list_signal"]

    # Signal 11: standards_review_linked
    sdr_ids = backlog_index.get(prop_id, [])
    if sdr_ids:
        reasons.append("standards_review_linked")
        raw_score += _SIGNAL_WEIGHTS["standards_review_linked"]

    # Cap score between 0.0 and 1.0.
    final_score = max(0.0, min(1.0, raw_score))
    return final_score, reasons, warnings


# ---------------------------------------------------------------------------
# Confidence and review status
# ---------------------------------------------------------------------------


def classify_confidence(score: float, reasons: list[str]) -> str:
    """Classify score into confidence level string."""
    if "standards_review_linked" in reasons and score < CONFIDENCE_LOW:
        return "review_required"
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_MEDIUM:
        return "medium"
    if score >= CONFIDENCE_LOW:
        return "low"
    return "review_required"


def _determine_review_status(
    reasons: list[str],
    warnings: list[str],
    confidence: str,
    existing_mapping_status: str,
) -> str:
    """Determine review_status for a candidate."""
    if existing_mapping_status in {
        "mapped_official_bms_xpath",
        "candidate_official_bms_xpath",
        "mapped",
    }:
        return "already_mapped"
    if "deleted_attribute_warning" in warnings:
        return "not_recommended"
    if confidence == "review_required":
        return "review_required"
    if "standards_review_linked" in reasons:
        return "review_required"
    return "proposed"


# ---------------------------------------------------------------------------
# Candidate building
# ---------------------------------------------------------------------------


def _make_candidate_id(webvoc_property_id: str, gdsn_bms_id: str) -> str:
    """Create a deterministic candidate_id string."""
    safe_prop = re.sub(r"[^a-zA-Z0-9_]", "_", webvoc_property_id)
    safe_bms = re.sub(r"[^a-zA-Z0-9_]", "_", str(gdsn_bms_id))
    return f"cand_{safe_prop}__{safe_bms}"


def _build_candidate_dict(
    webvoc_property: dict,
    gdsn_attribute: dict,
    score: float,
    reasons: list[str],
    warnings: list[str],
    catalog_index: dict,
    backlog_index: dict,
) -> dict:
    """Assemble the full candidate dict from all inputs."""
    prop_id = str(webvoc_property.get("term_id") or "").strip()
    bms_id = str(gdsn_attribute.get("bms_id") or "").strip()
    confidence = classify_confidence(score, reasons)

    # Determine existing mapping status.
    catalog_hits = catalog_index.get(prop_id, [])
    existing_mapping_status = ""
    existing_mapping_field = ""
    existing_mapping_confidence = ""
    if catalog_hits:
        # Use the highest-confidence row.
        best = sorted(
            catalog_hits,
            key=lambda r: (
                r.get("confidence") == "high",
                r.get("mapping_status", "") in {"mapped_official_bms_xpath", "mapped"},
            ),
            reverse=True,
        )[0]
        existing_mapping_status = str(best.get("mapping_status") or "")
        existing_mapping_field = str(best.get("canonical_field") or "")
        existing_mapping_confidence = str(best.get("confidence") or "")

    review_status = _determine_review_status(
        reasons,
        warnings,
        confidence,
        existing_mapping_status,
    )

    # SDR linked IDs.
    linked_sdr_ids = backlog_index.get(prop_id, [])

    blocking_notes: list[str] = []
    if "deleted_attribute_warning" in warnings:
        blocking_notes.append("GDSN attribute is marked deleted; not recommended for new mappings.")
    if "datatype_mismatch_warning" in warnings:
        blocking_notes.append("Range/DataType mismatch detected; semantic review required.")
    if "class_row_not_attribute" in warnings:
        blocking_notes.append("Row is Class/Module type, not a leaf Attribute.")

    is_deleted = str(gdsn_attribute.get("is_deleted") or "false").strip().lower() == "true"
    is_candidate_source = str(gdsn_attribute.get("is_candidate_source") or "false").strip().lower() == "true"

    source_message = str(gdsn_attribute.get("message") or "").strip()

    return {
        "candidate_id": _make_candidate_id(prop_id, bms_id),
        "webvoc_property_id": prop_id,
        "webvoc_compact_name": str(webvoc_property.get("compact_name") or "").strip(),
        "webvoc_label": str(webvoc_property.get("label") or "").strip(),
        "webvoc_comment": str(webvoc_property.get("comment") or "").strip(),
        "webvoc_domain": str(webvoc_property.get("domain") or "").strip(),
        "webvoc_range": str(webvoc_property.get("range") or "").strip(),
        "gdsn_bms_id": bms_id,
        "gdsn_attribute_name": str(gdsn_attribute.get("attribute_name") or "").strip(),
        "gdsn_xpath": str(gdsn_attribute.get("xpath") or "").strip(),
        "gdsn_module": str(gdsn_attribute.get("module") or "").strip(),
        "gdsn_parent_class": str(gdsn_attribute.get("parent_class") or "").strip(),
        "gdsn_data_type": str(gdsn_attribute.get("data_type") or "").strip(),
        "gdsn_multiplicity": str(gdsn_attribute.get("multiplicity") or "").strip(),
        "gdsn_code_list_name": str(gdsn_attribute.get("code_list_name") or "").strip(),
        "gdsn_bms_code_list_id": str(gdsn_attribute.get("bms_code_list_id") or "").strip(),
        "gdsn_semantic_resource_urn": str(gdsn_attribute.get("semantic_resource_urn") or "").strip(),
        "gdsn_definition": str(gdsn_attribute.get("definition") or "").strip(),
        "source_message": source_message,
        "is_deleted": is_deleted,
        "is_candidate_source": is_candidate_source,
        "existing_mapping_status": existing_mapping_status,
        "existing_mapping_field": existing_mapping_field,
        "existing_mapping_confidence": existing_mapping_confidence,
        "standards_review_status": (
            "open" if linked_sdr_ids else ""
        ),
        "linked_sdr_ids": linked_sdr_ids,
        "score": round(score, 4),
        "confidence_level": confidence,
        "review_status": review_status,
        "reasons": reasons,
        "warnings": warnings,
        "blocking_notes": blocking_notes,
        "created_by_version": CREATED_BY_VERSION,
    }


def generate_candidates_for_property(
    property_id: str,
    inputs: dict,
    limit: int = 20,
) -> list[dict]:
    """Generate candidate GDSN attributes for a single WebVoc property.

    Parameters
    ----------
    property_id:
        The term_id of the WebVoc property, e.g. ``gs1:gtin``.
    inputs:
        Loaded and indexed inputs from :func:`build_candidate_inputs`.
    limit:
        Maximum number of candidates to return per property.

    Returns
    -------
    list[dict]
        Candidates sorted by score descending, then by gdsn_bms_id ascending
        for determinism.
    """
    # Find the WebVoc property row.
    webvoc_property = next(
        (row for row in inputs["webvoc_rows"] if row.get("term_id") == property_id),
        None,
    )
    if webvoc_property is None:
        return []

    gdsn_rows = inputs["gdsn_rows"]
    catalog_index = inputs["catalog_index"]
    backlog_index = inputs["backlog_property_index"]

    # Score all GDSN rows (including non-candidate rows for completeness).
    scored: list[tuple[float, str, dict]] = []
    for gdsn_row in gdsn_rows:
        score, reasons, warnings = score_candidate(
            webvoc_property,
            gdsn_row,
            inputs,
        )
        # Only include rows with any positive signal OR that already appear
        # in catalog as mapped.
        if score > 0 or reasons:
            candidate = _build_candidate_dict(
                webvoc_property,
                gdsn_row,
                score,
                reasons,
                warnings,
                catalog_index,
                backlog_index,
            )
            bms_id_str = str(gdsn_row.get("bms_id") or "0")
            try:
                bms_sort = int(bms_id_str)
            except ValueError:
                bms_sort = 0
            scored.append((score, bms_sort, candidate))

    # Sort: descending score, then ascending bms_id for determinism.
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [item[2] for item in scored[:limit]]


def generate_all_candidates(
    inputs: dict,
    limit_per_property: int = 20,
) -> list[dict]:
    """Generate candidates for all WebVoc properties.

    Parameters
    ----------
    inputs:
        Loaded and indexed inputs from :func:`build_candidate_inputs`.
    limit_per_property:
        Maximum candidates per property.

    Returns
    -------
    list[dict]
        All candidates, ordered by property term_id (alphabetically), then
        by score descending.
    """
    all_candidates: list[dict] = []
    # Sort properties deterministically by term_id.
    sorted_properties = sorted(
        inputs["webvoc_rows"],
        key=lambda r: str(r.get("term_id") or ""),
    )
    for prop_row in sorted_properties:
        prop_id = str(prop_row.get("term_id") or "").strip()
        if not prop_id:
            continue
        candidates = generate_candidates_for_property(prop_id, inputs, limit=limit_per_property)
        all_candidates.extend(candidates)
    return all_candidates


# ---------------------------------------------------------------------------
# Filtering helpers
# ---------------------------------------------------------------------------


def filter_candidates(
    candidates: list[dict],
    min_confidence: str = "low",
    include_low_confidence: bool = True,
    include_review_required: bool = True,
) -> list[dict]:
    """Filter candidates by minimum confidence level.

    Parameters
    ----------
    min_confidence:
        Minimum confidence level to include: ``high``, ``medium``, ``low``.
    include_low_confidence:
        If False, exclude ``low`` confidence candidates.
    include_review_required:
        If True, include ``review_required`` candidates regardless of score.
    """
    order = ["high", "medium", "low", "review_required"]
    try:
        threshold_idx = order.index(min_confidence)
    except ValueError:
        threshold_idx = order.index("low")

    result = []
    for c in candidates:
        level = c.get("confidence_level", "review_required")
        if level == "review_required":
            if include_review_required:
                result.append(c)
            continue
        try:
            level_idx = order.index(level)
        except ValueError:
            continue
        if level_idx > threshold_idx:
            continue
        if level == "low" and not include_low_confidence:
            continue
        result.append(c)
    return result


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def generate_candidate_summary(candidates: list[dict]) -> dict:
    """Build summary counts from a list of candidates."""
    total = len(candidates)
    counts_by_confidence: dict[str, int] = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "review_required": 0,
    }
    counts_by_review_status: dict[str, int] = {
        "proposed": 0,
        "already_mapped": 0,
        "review_required": 0,
        "not_recommended": 0,
    }
    properties_covered: set[str] = set()
    for c in candidates:
        level = c.get("confidence_level", "review_required")
        counts_by_confidence[level] = counts_by_confidence.get(level, 0) + 1
        status = c.get("review_status", "proposed")
        counts_by_review_status[status] = counts_by_review_status.get(status, 0) + 1
        prop_id = c.get("webvoc_property_id", "")
        if prop_id:
            properties_covered.add(prop_id)

    return {
        "total_candidates": total,
        "properties_covered": len(properties_covered),
        "by_confidence": counts_by_confidence,
        "by_review_status": counts_by_review_status,
        "created_by_version": CREATED_BY_VERSION,
    }


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def candidate_to_dict(candidate: dict) -> dict:
    """Return a flat, serialization-friendly copy of a candidate dict."""
    flat = dict(candidate)
    # Flatten list fields to joined strings for CSV compatibility.
    flat["reasons"] = "; ".join(candidate.get("reasons") or [])
    flat["warnings"] = "; ".join(candidate.get("warnings") or [])
    flat["blocking_notes"] = "; ".join(candidate.get("blocking_notes") or [])
    flat["linked_sdr_ids"] = "; ".join(str(s) for s in (candidate.get("linked_sdr_ids") or []))
    return flat


def candidate_report_bytes_json(candidates: list[dict]) -> bytes:
    """Serialize candidates list to UTF-8 JSON bytes."""
    return json.dumps(candidates, indent=2, ensure_ascii=False).encode("utf-8")


def candidate_report_bytes_csv(candidates: list[dict]) -> bytes:
    """Serialize candidates list to UTF-8 CSV bytes."""
    if not candidates:
        return b""
    rows = [candidate_to_dict(c) for c in candidates]
    fieldnames = list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def candidate_report_bytes_xlsx(candidates: list[dict]) -> bytes:
    """Serialize candidates list to XLSX bytes using openpyxl."""
    try:
        import openpyxl
    except ImportError:
        return b""

    rows = [candidate_to_dict(c) for c in candidates]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mapping Candidates"
    if not rows:
        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    fieldnames = list(rows[0].keys())
    ws.append(fieldnames)
    for row in rows:
        ws.append([str(row.get(f, "") or "") for f in fieldnames])

    # Auto-size columns (approximate).
    for col_cells in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 50)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ---------------------------------------------------------------------------
# File-system output
# ---------------------------------------------------------------------------


def write_candidate_reports(
    candidates: list[dict],
    output_dir: str,
    formats: list[str] | None = None,
) -> dict[str, str]:
    """Write candidate reports to output_dir.

    Parameters
    ----------
    candidates:
        Candidate dicts from :func:`generate_all_candidates` or
        :func:`generate_candidates_for_property`.
    output_dir:
        Directory path.  Created if it does not exist.
    formats:
        List of ``"json"``, ``"csv"``, ``"xlsx"``.  Defaults to ``["json", "csv"]``.

    Returns
    -------
    dict[str, str]
        Mapping of format -> file path.
    """
    if formats is None:
        formats = ["json", "csv"]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    if "json" in formats:
        p = out / "mapping_candidates.json"
        p.write_bytes(candidate_report_bytes_json(candidates))
        paths["json"] = str(p)

    if "csv" in formats:
        p = out / "mapping_candidates.csv"
        p.write_bytes(candidate_report_bytes_csv(candidates))
        paths["csv"] = str(p)

    if "xlsx" in formats:
        xlsx_bytes = candidate_report_bytes_xlsx(candidates)
        if xlsx_bytes:
            p = out / "mapping_candidates.xlsx"
            p.write_bytes(xlsx_bytes)
            paths["xlsx"] = str(p)

    # Always write a summary.
    summary = generate_candidate_summary(candidates)
    summary_path = out / "mapping_candidates_summary.json"
    summary_path.write_bytes(json.dumps(summary, indent=2).encode("utf-8"))
    paths["summary"] = str(summary_path)

    return paths
