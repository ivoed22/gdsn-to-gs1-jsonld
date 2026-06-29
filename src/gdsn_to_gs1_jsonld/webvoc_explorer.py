"""Offline GS1 Web Vocabulary explorer data preparation."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


COVERAGE_STATUSES = (
    "mapped",
    "high_confidence",
    "candidate",
    "experimental",
    "standards_review_required",
    "schema_org_fallback",
    "unmapped",
    "unknown",
)

PROPERTY_GROUPS = (
    "Core Product Information",
    "Classification & Links",
    "Physical Dimensions",
    "Digital Links & Services",
    "Provenance and Claims",
    "Packaging Details",
    "Food, Beverage & Tobacco",
    "Nutritional Information",
    "Allergens",
    "Certifications",
    "Documents and DPP",
    "Organization and Place",
    "Offer and Sales Information",
    "Traceability and Lifecycle",
    "Other Web Vocabulary Properties",
)

DEFAULT_WEBVOC_PATH = Path("webvoc/current/gs1Voc.jsonld")
DEFAULT_LINKTYPES_PATH = Path("webvoc/current/linktypes.json")
DEFAULT_METADATA_PATH = Path("webvoc/current/metadata.json")
DEFAULT_CATALOG_PATH = Path(
    "mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
)
DEFAULT_BACKLOG_PATH = Path("docs/standards-decisions/standards_review_backlog.json")

_PROPERTY_PATTERN = re.compile(r"(?:gs1|schema):[A-Za-z][A-Za-z0-9_-]*")


@dataclass(frozen=True)
class VocabularyClass:
    term_id: str
    compact_name: str
    full_iri: str
    label: str
    comment: str
    types: list[str]
    sub_class_of: list[str]
    term_status: str


@dataclass(frozen=True)
class MappingEvidence:
    canonical_field: str
    jsonld_property: str
    mapping_status: str
    confidence: str
    mapping_version: str
    mapping_profile: str
    scope_group: str
    bms_id: str
    gdsn_xpath: str
    source_attribute_name: str
    source: str


@dataclass(frozen=True)
class GovernanceReference:
    sdr_id: str
    title: str
    category: str
    status: str
    warning_count: int
    affected_fields: list[str]
    issue_url: str
    decision_file: str


@dataclass(frozen=True)
class VocabularyProperty:
    term_id: str
    compact_name: str
    full_iri: str
    label: str
    comment: str
    domain: list[str]
    range: list[str]
    sub_property_of: list[str]
    types: list[str]
    term_status: str
    is_link_type: bool
    group: str
    coverage_status: str
    evidence: list[MappingEvidence] = field(default_factory=list)
    governance: list[GovernanceReference] = field(default_factory=list)


@dataclass(frozen=True)
class ExplorerDataset:
    metadata: dict[str, Any]
    summary: dict[str, Any]
    classes: list[VocabularyClass]
    properties: list[VocabularyProperty]


def load_webvoc_jsonld(path: str | Path = DEFAULT_WEBVOC_PATH) -> dict[str, Any]:
    """Load the local Web Vocabulary JSON-LD snapshot."""
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_webvoc_metadata(path: str | Path = DEFAULT_METADATA_PATH) -> dict[str, Any]:
    metadata_path = Path(path)
    if not metadata_path.is_file():
        return {}
    loaded = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    return loaded if isinstance(loaded, dict) else {}


def load_linktypes(path: str | Path = DEFAULT_LINKTYPES_PATH) -> dict[str, dict[str, Any]]:
    linktypes_path = Path(path)
    if not linktypes_path.is_file():
        return {}
    loaded = json.loads(linktypes_path.read_text(encoding="utf-8-sig"))
    if not isinstance(loaded, dict):
        return {}
    return {
        str(key): value
        for key, value in loaded.items()
        if isinstance(value, dict)
    }


def load_mapping_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> list[dict[str, str]]:
    """Load the mapping catalog as plain dictionaries."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_sdr_backlog(path: str | Path = DEFAULT_BACKLOG_PATH) -> list[dict[str, Any]]:
    backlog_path = Path(path)
    if not backlog_path.is_file():
        return []
    loaded = json.loads(backlog_path.read_text(encoding="utf-8-sig"))
    return [item for item in loaded if isinstance(item, dict)] if isinstance(loaded, list) else []


def _graph(data: dict[str, Any]) -> list[dict[str, Any]]:
    graph = data.get("@graph", [])
    if not isinstance(graph, list):
        return []
    return [item for item in graph if isinstance(item, dict)]


def _types(item: dict[str, Any]) -> list[str]:
    value = item.get("@type")
    if isinstance(value, list):
        return [str(entry) for entry in value]
    if value is None:
        return []
    return [str(value)]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "@value" in value:
            return str(value["@value"])
        if "@id" in value:
            return str(value["@id"])
        if "@list" in value:
            return ", ".join(_values(value["@list"]))
        return ""
    if isinstance(value, list):
        return "; ".join(item for item in (_text(entry) for entry in value) if item)
    return str(value)


def _values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        values: list[str] = []
        for entry in value:
            values.extend(_values(entry))
        return values
    if isinstance(value, dict):
        if "@id" in value:
            return [str(value["@id"])]
        if "@value" in value:
            return [str(value["@value"])]
        if "@list" in value:
            return _values(value["@list"])
        return []
    return [str(value)]


def _compact_name(term_id: str) -> str:
    return term_id.split(":", 1)[1] if ":" in term_id else term_id


def _full_iri(term_id: str, item: dict[str, Any]) -> str:
    for key in ("owl:equivalentProperty", "owl:equivalentClass"):
        values = _values(item.get(key))
        for value in values:
            if value.startswith("https://gs1.org/voc/"):
                return value
    if term_id.startswith("gs1:"):
        return "https://gs1.org/voc/" + _compact_name(term_id)
    if term_id.startswith("schema:"):
        return "https://schema.org/" + _compact_name(term_id)
    return term_id


def _is_class(item: dict[str, Any]) -> bool:
    item_types = set(_types(item))
    return bool({"owl:Class", "rdfs:Class"} & item_types)


def _is_property(item: dict[str, Any]) -> bool:
    item_types = set(_types(item))
    return bool({"rdf:Property", "owl:ObjectProperty", "owl:DatatypeProperty"} & item_types)


def extract_classes(data: dict[str, Any]) -> list[VocabularyClass]:
    """Extract Web Vocabulary classes from the JSON-LD graph."""
    classes: list[VocabularyClass] = []
    for item in _graph(data):
        term_id = item.get("@id")
        if not isinstance(term_id, str) or not term_id.startswith("gs1:"):
            continue
        if not _is_class(item):
            continue
        classes.append(
            VocabularyClass(
                term_id=term_id,
                compact_name=_compact_name(term_id),
                full_iri=_full_iri(term_id, item),
                label=_text(item.get("rdfs:label")),
                comment=_text(item.get("rdfs:comment")),
                types=_types(item),
                sub_class_of=_values(item.get("rdfs:subClassOf")),
                term_status=_text(item.get("sw:term_status")),
            )
        )
    return sorted(classes, key=lambda item: item.term_id.lower())


def _row_property_terms(row: dict[str, str]) -> set[str]:
    fields = (
        row.get("jsonld_property", ""),
        row.get("recommended_jsonld_property", ""),
        row.get("webvoc_property_validation", ""),
    )
    terms: set[str] = set()
    for field in fields:
        terms.update(_PROPERTY_PATTERN.findall(field or ""))
    return terms


def _catalog_by_property(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    catalog: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        for term in _row_property_terms(row):
            catalog[term].append(row)
    return dict(catalog)


def _evidence_from_row(row: dict[str, str]) -> MappingEvidence:
    return MappingEvidence(
        canonical_field=row.get("canonical_field", ""),
        jsonld_property=row.get("jsonld_property", ""),
        mapping_status=row.get("mapping_status", ""),
        confidence=row.get("confidence", ""),
        mapping_version=row.get("mapping_version", ""),
        mapping_profile=row.get("technical_mapping_file", ""),
        scope_group=row.get("scope_group", ""),
        bms_id=row.get("gdsn_bms_id", ""),
        gdsn_xpath=row.get("gdsn_xpath", ""),
        source_attribute_name=row.get("gdsn_attribute_name", ""),
        source=row.get("source", ""),
    )


def _coverage_for_row(row: dict[str, str]) -> str:
    mapping_status = row.get("mapping_status", "").strip().lower()
    confidence = row.get("confidence", "").strip().lower()
    webvoc_status = row.get("webvoc_property_status", "").strip().lower()
    webvoc_validation = row.get("webvoc_property_validation", "").strip().lower()
    review_action = row.get("review_action", "").strip().lower()
    jsonld_property = row.get("jsonld_property", "")
    recommended = row.get("recommended_jsonld_property", "")

    if "schema:" in jsonld_property or (
        "schema:" in recommended and "gs1:" not in jsonld_property
    ):
        return "schema_org_fallback"
    if mapping_status == "experimental":
        return "experimental"
    if (
        "review" in mapping_status
        or "needs" in mapping_status
        or "not found" in webvoc_validation
        or webvoc_status in {"webvoc_missing", "webvoc_review_required"}
        or (review_action and review_action not in {"ok", "none"})
    ):
        return "standards_review_required"
    if mapping_status.startswith("candidate"):
        return "candidate"
    if mapping_status.startswith("mapped") and confidence == "high":
        return "high_confidence"
    if mapping_status.startswith("mapped"):
        return "mapped"
    if mapping_status:
        return "unknown"
    return "unmapped"


def _combine_coverage(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "unmapped"
    priority = {
        "standards_review_required": 7,
        "schema_org_fallback": 6,
        "experimental": 5,
        "candidate": 4,
        "high_confidence": 3,
        "mapped": 2,
        "unknown": 1,
        "unmapped": 0,
    }
    statuses = [_coverage_for_row(row) for row in rows]
    return max(statuses, key=lambda status: priority[status])


def _governance_by_property(backlog: Iterable[dict[str, Any]]) -> dict[str, list[GovernanceReference]]:
    references: dict[str, list[GovernanceReference]] = defaultdict(list)
    for item in backlog:
        properties = item.get("affected_properties", [])
        if not isinstance(properties, list):
            continue
        reference = GovernanceReference(
            sdr_id=str(item.get("id", "")),
            title=str(item.get("title", "")),
            category=str(item.get("category", "")),
            status=str(item.get("status", "")),
            warning_count=int(item.get("warning_count") or 0),
            affected_fields=[
                str(field)
                for field in item.get("affected_fields", [])
                if isinstance(field, str)
            ],
            issue_url=str(item.get("issue_url", "")),
            decision_file=str(item.get("decision_file", "")),
        )
        for property_id in properties:
            if isinstance(property_id, str):
                references[property_id].append(reference)
    return dict(references)


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def group_property(
    term_id: str,
    *,
    label: str = "",
    comment: str = "",
    domain: Iterable[str] = (),
    range_values: Iterable[str] = (),
    sub_property_of: Iterable[str] = (),
    is_link_type: bool = False,
    evidence: Iterable[MappingEvidence] = (),
) -> str:
    """Assign a pragmatic review group for a Web Vocabulary property.

    The grouping is intentionally heuristic. It combines term names, labels,
    comments, domain/range, sub-property relations, link-type status, and
    catalog scope/canonical context so the Explorer is useful for standards
    review without pretending to define a normative GS1 taxonomy.
    """
    evidence_text = " ".join(
        " ".join(
            (
                item.canonical_field,
                item.scope_group,
                item.source_attribute_name,
                item.jsonld_property,
            )
        )
        for item in evidence
    )
    text = " ".join(
        [
            term_id,
            label,
            comment,
            " ".join(domain),
            " ".join(range_values),
            " ".join(sub_property_of),
            evidence_text,
        ]
    ).lower()

    if _contains_any(text, ("nutrient", "nutrition", "calorie", "energy")):
        return "Nutritional Information"
    if _contains_any(text, ("allergen", "allergy", "containment")):
        return "Allergens"
    if _contains_any(text, ("certification", "certificate", "certified", "accreditation")):
        return "Certifications"
    if _contains_any(text, ("document", "referencedfile", "file type", "dpp", "passport")):
        return "Documents and DPP"
    if _contains_any(text, ("food", "beverage", "tobacco", "ingredient", "diet")):
        return "Food, Beverage & Tobacco"
    if _contains_any(
        text,
        ("dimension", "height", "width", "depth", "weight", "measurement", "netcontent"),
    ):
        return "Physical Dimensions"
    if _contains_any(text, ("packag", "case", "pallet", "container", "label")):
        return "Packaging Details"
    if _contains_any(text, ("organization", "organisation", "place", "location", "address", "contact")):
        return "Organization and Place"
    if _contains_any(text, ("offer", "price", "sales", "sell", "order", "payment", "invoice")):
        return "Offer and Sales Information"
    if _contains_any(text, ("trace", "lifecycle", "life cycle", "batch", "lot", "serial", "expiry", "production")):
        return "Traceability and Lifecycle"
    if _contains_any(text, ("claim", "provenance", "organic", "halal", "kosher", "sustainab")):
        return "Provenance and Claims"
    if is_link_type or _contains_any(text, ("linktype", "digital link", "url", "website", "service")):
        return "Digital Links & Services"
    if _contains_any(text, ("classification", "category", "gpc", "code", "sameas")):
        return "Classification & Links"
    if _contains_any(text, ("gtin", "product", "brand", "description", "name")):
        return "Core Product Information"
    return "Other Web Vocabulary Properties"


def _is_link_type(
    term_id: str,
    sub_property_of: Iterable[str],
    linktypes: dict[str, dict[str, Any]],
) -> bool:
    local_name = _compact_name(term_id)
    return "gs1:linkType" in set(sub_property_of) or local_name in linktypes


def extract_properties(
    data: dict[str, Any],
    *,
    catalog_rows: Iterable[dict[str, str]] = (),
    backlog: Iterable[dict[str, Any]] = (),
    linktypes: dict[str, dict[str, Any]] | None = None,
) -> list[VocabularyProperty]:
    """Extract properties and attach catalog and SDR review context."""
    linktypes = linktypes or {}
    catalog_index = _catalog_by_property(catalog_rows)
    governance_index = _governance_by_property(backlog)
    properties: list[VocabularyProperty] = []
    for item in _graph(data):
        term_id = item.get("@id")
        if not isinstance(term_id, str) or not term_id.startswith("gs1:"):
            continue
        if not _is_property(item):
            continue
        domain = _values(item.get("rdfs:domain"))
        range_values = _values(item.get("rdfs:range"))
        sub_property_of = _values(item.get("rdfs:subPropertyOf"))
        evidence = [_evidence_from_row(row) for row in catalog_index.get(term_id, [])]
        is_link_type = _is_link_type(term_id, sub_property_of, linktypes)
        label = _text(item.get("rdfs:label"))
        comment = _text(item.get("rdfs:comment"))
        properties.append(
            VocabularyProperty(
                term_id=term_id,
                compact_name=_compact_name(term_id),
                full_iri=_full_iri(term_id, item),
                label=label,
                comment=comment,
                domain=domain,
                range=range_values,
                sub_property_of=sub_property_of,
                types=_types(item),
                term_status=_text(item.get("sw:term_status")),
                is_link_type=is_link_type,
                group=group_property(
                    term_id,
                    label=label,
                    comment=comment,
                    domain=domain,
                    range_values=range_values,
                    sub_property_of=sub_property_of,
                    is_link_type=is_link_type,
                    evidence=evidence,
                ),
                coverage_status=_combine_coverage(catalog_index.get(term_id, [])),
                evidence=evidence,
                governance=governance_index.get(term_id, []),
            )
        )
    return sorted(properties, key=lambda item: (item.group, item.term_id.lower()))


def build_explorer_dataset(
    *,
    webvoc_path: str | Path = DEFAULT_WEBVOC_PATH,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
    backlog_path: str | Path = DEFAULT_BACKLOG_PATH,
    metadata_path: str | Path = DEFAULT_METADATA_PATH,
    linktypes_path: str | Path = DEFAULT_LINKTYPES_PATH,
) -> ExplorerDataset:
    """Build the complete offline Explorer dataset."""
    webvoc = load_webvoc_jsonld(webvoc_path)
    metadata = load_webvoc_metadata(metadata_path)
    catalog_rows = load_mapping_catalog(catalog_path)
    backlog = load_sdr_backlog(backlog_path)
    linktypes = load_linktypes(linktypes_path)
    classes = extract_classes(webvoc)
    properties = extract_properties(
        webvoc,
        catalog_rows=catalog_rows,
        backlog=backlog,
        linktypes=linktypes,
    )
    coverage_counts = Counter(item.coverage_status for item in properties)
    group_counts = Counter(item.group for item in properties)
    mapped_count = coverage_counts["mapped"] + coverage_counts["high_confidence"]
    review_count = sum(
        1
        for item in properties
        if item.coverage_status == "standards_review_required" or item.governance
    )
    summary = {
        "webvoc_version": metadata.get("detected_version", ""),
        "webvoc_last_modified": metadata.get("detected_last_modified", ""),
        "class_count": len(classes),
        "property_count": len(properties),
        "mapped_property_count": mapped_count,
        "standards_review_property_count": review_count,
        "link_type_property_count": sum(1 for item in properties if item.is_link_type),
        "catalog_row_count": len(catalog_rows),
        "sdr_reference_count": sum(len(item.governance) for item in properties),
        "coverage_counts": {status: coverage_counts[status] for status in COVERAGE_STATUSES},
        "group_counts": {group: group_counts[group] for group in PROPERTY_GROUPS},
        "offline": True,
    }
    return ExplorerDataset(
        metadata=metadata,
        summary=summary,
        classes=classes,
        properties=properties,
    )


def property_to_row(item: VocabularyProperty) -> dict[str, Any]:
    evidence = item.evidence
    governance = item.governance
    return {
        "Group": item.group,
        "Property": item.term_id,
        "Label": item.label,
        "Domain": "; ".join(item.domain),
        "Range": "; ".join(item.range),
        "Coverage": item.coverage_status,
        "BMS/XPath evidence": "yes" if any(e.bms_id or e.gdsn_xpath for e in evidence) else "no",
        "SDR indicator": ", ".join(ref.sdr_id for ref in governance),
        "Evidence count": len(evidence),
        "Full IRI": item.full_iri,
        "Comment": item.comment,
        "SubPropertyOf": "; ".join(item.sub_property_of),
        "Type": "; ".join(item.types),
        "Link type": item.is_link_type,
    }


def filter_properties(
    properties: Iterable[VocabularyProperty],
    *,
    group: str = "All groups",
    coverage_status: str = "All statuses",
    search: str = "",
    only_mapped: bool = False,
    only_standards_review: bool = False,
) -> list[VocabularyProperty]:
    """Filter Explorer properties for the Streamlit UI and tests."""
    normalized_search = search.strip().lower()
    filtered: list[VocabularyProperty] = []
    for item in properties:
        if group not in {"", "All groups"} and item.group != group:
            continue
        if coverage_status not in {"", "All statuses"} and item.coverage_status != coverage_status:
            continue
        if only_mapped and item.coverage_status not in {"mapped", "high_confidence"}:
            continue
        if only_standards_review and not (
            item.coverage_status == "standards_review_required" or item.governance
        ):
            continue
        if normalized_search:
            haystack = " ".join(
                (
                    item.term_id,
                    item.label,
                    item.comment,
                    " ".join(item.domain),
                    " ".join(item.range),
                    " ".join(e.canonical_field for e in item.evidence),
                    " ".join(e.source_attribute_name for e in item.evidence),
                )
            ).lower()
            if normalized_search not in haystack:
                continue
        filtered.append(item)
    return filtered


def _json_ready_dataset(dataset: ExplorerDataset) -> dict[str, Any]:
    return {
        "metadata": dataset.metadata,
        "summary": dataset.summary,
        "classes": [asdict(item) for item in dataset.classes],
        "properties": [asdict(item) for item in dataset.properties],
    }


def _summary_xlsx_bytes(dataset: ExplorerDataset) -> bytes:
    buffer = BytesIO()
    property_rows = [property_to_row(item) for item in dataset.properties]
    class_rows = [asdict(item) for item in dataset.classes]
    coverage_rows = [
        {"coverage_status": key, "count": value}
        for key, value in dataset.summary["coverage_counts"].items()
    ]
    group_rows = [
        {"group": key, "count": value}
        for key, value in dataset.summary["group_counts"].items()
    ]
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([dataset.summary]).to_excel(
            writer,
            index=False,
            sheet_name="Summary",
        )
        pd.DataFrame(property_rows).to_excel(
            writer,
            index=False,
            sheet_name="Properties",
        )
        pd.DataFrame(class_rows).to_excel(
            writer,
            index=False,
            sheet_name="Classes",
        )
        pd.DataFrame(coverage_rows).to_excel(
            writer,
            index=False,
            sheet_name="Coverage",
        )
        pd.DataFrame(group_rows).to_excel(
            writer,
            index=False,
            sheet_name="Groups",
        )
    return buffer.getvalue()


def write_webvoc_explorer_outputs(
    dataset: ExplorerDataset,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write deterministic Explorer JSON, CSV, summary JSON, and XLSX outputs."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "properties_json": directory / "webvoc_explorer_properties.json",
        "properties_csv": directory / "webvoc_explorer_properties.csv",
        "summary_json": directory / "webvoc_explorer_summary.json",
        "summary_xlsx": directory / "webvoc_explorer_summary.xlsx",
    }
    properties = [asdict(item) for item in dataset.properties]
    paths["properties_json"].write_text(
        json.dumps(properties, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    pd.DataFrame([property_to_row(item) for item in dataset.properties]).to_csv(
        paths["properties_csv"],
        index=False,
        encoding="utf-8",
    )
    paths["summary_json"].write_text(
        json.dumps(
            {
                "metadata": dataset.metadata,
                "summary": dataset.summary,
                "class_count": len(dataset.classes),
                "property_count": len(dataset.properties),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    paths["summary_xlsx"].write_bytes(_summary_xlsx_bytes(dataset))
    return paths
