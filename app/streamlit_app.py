from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_DIRECTORY = REPOSITORY_ROOT / "src"


def _ensure_import_paths() -> None:
    """Make local package imports work in Streamlit Cloud script execution."""
    for directory in (REPOSITORY_ROOT, SRC_DIRECTORY):
        directory_path = str(directory)
        if directory_path not in sys.path:
            sys.path.insert(0, directory_path)


_ensure_import_paths()

from gdsn_to_gs1_jsonld.batch_converter import (
    BatchConversionError,
    BatchConversionLimits,
    convert_batch_zip,
)
from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.jsonld_builder import (
    build_empty_builder_state,
    get_builder_fields,
    get_builder_groups,
    infer_input_type,
    jsonld_bytes as prototype_jsonld_bytes,
    load_builder_manifest,
    serialize_builder_state_to_jsonld,
    update_builder_value,
    validate_builder_state,
)
from gdsn_to_gs1_jsonld.reporter import json_bytes, mapping_report_xlsx_bytes
from gdsn_to_gs1_jsonld.webvoc_explorer import (
    COVERAGE_STATUSES,
    PROPERTY_GROUPS,
    build_explorer_dataset,
    filter_properties,
    property_to_row,
)
from gdsn_to_gs1_jsonld.xml_parser import XMLParseError
from app.ui import (
    APP_VERSION,
    apply_page_styles,
    render_download_intro,
    render_empty_upload_state,
    render_identity_card,
    render_page_header,
    render_preview_heading,
    render_result_summary,
    render_review_guidance,
    render_section_header,
    render_status_card,
    render_standards_backlog_status,
    render_vocabulary_status,
    render_workflow_entry_intro,
    render_workflow_mode_card,
    render_workflow_overview,
)

RESULT_STATE_KEYS = (
    "conversion_result",
    "jsonld_bytes",
    "mapping_report_bytes",
    "validation_report_bytes",
    "unmapped_fields_bytes",
    "output_name_base",
)
BATCH_RESULT_STATE_KEYS = (
    "batch_conversion_report",
    "batch_export_zip_bytes",
)
WORKFLOW_MODES = (
    {
        "key": "convert",
        "title": "Convert GDSN XML",
        "marker": "XML",
        "description": (
            "Convert a single product message or a ZIP batch with the active "
            "mapping profile and evidence reports."
        ),
        "outcome": "JSON-LD plus mapping, validation, and unmapped-field evidence.",
    },
    {
        "key": "explore",
        "title": "Explore GS1 Web Vocabulary",
        "marker": "VOC",
        "description": (
            "Browse the local GS1 Web Vocabulary snapshot and inspect mapping "
            "coverage, BMS/XPath evidence, and SDR context."
        ),
        "outcome": "Read-only vocabulary review with local catalog evidence.",
    },
    {
        "key": "prototype",
        "title": "Create JSON-LD Prototype",
        "marker": "LD",
        "description": (
            "Manually select GS1 Web Vocabulary properties, enter values, and "
            "preview prototype JSON-LD live."
        ),
        "outcome": (
            "Manual JSON-LD prototype with visible governance and traceability "
            "warning."
        ),
    },
    {
        "key": "standards",
        "title": "Standards Review",
        "marker": "SDR",
        "description": (
            "Inspect open standards and governance decisions from the existing "
            "SDR backlog."
        ),
        "outcome": "Read-only SDR status without changing converter behavior.",
    },
)
DEFAULT_WORKFLOW_MODE = WORKFLOW_MODES[0]["title"]


def clear_results() -> None:
    for key in RESULT_STATE_KEYS:
        st.session_state.pop(key, None)


def clear_batch_results() -> None:
    for key in BATCH_RESULT_STATE_KEYS:
        st.session_state.pop(key, None)


def clear_all_results() -> None:
    clear_results()
    clear_batch_results()


def set_workflow_mode(mode: str) -> None:
    st.session_state["workflow_mode"] = mode


def _load_webvoc_metadata() -> dict:
    webvoc_metadata_path = REPOSITORY_ROOT / "webvoc" / "current" / "metadata.json"
    if not webvoc_metadata_path.is_file():
        return {}
    try:
        return json.loads(webvoc_metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _load_open_standards_backlog() -> list[dict]:
    backlog_path = (
        REPOSITORY_ROOT
        / "docs"
        / "standards-decisions"
        / "standards_review_backlog.json"
    )
    if not backlog_path.is_file():
        return []
    try:
        loaded_backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(loaded_backlog, list):
        return []
    return [
        item
        for item in loaded_backlog
        if isinstance(item, dict) and item.get("status") == "open"
    ]


@st.cache_data(show_spinner=False)
def _load_webvoc_explorer_dataset() -> object:
    return build_explorer_dataset(
        webvoc_path=REPOSITORY_ROOT / "webvoc" / "current" / "gs1Voc.jsonld",
        catalog_path=(
            REPOSITORY_ROOT
            / "mapping_catalog"
            / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
        ),
        backlog_path=(
            REPOSITORY_ROOT
            / "docs"
            / "standards-decisions"
            / "standards_review_backlog.json"
        ),
        metadata_path=REPOSITORY_ROOT / "webvoc" / "current" / "metadata.json",
        linktypes_path=REPOSITORY_ROOT / "webvoc" / "current" / "linktypes.json",
    )


@st.cache_data(show_spinner=False)
def _load_builder_manifest() -> dict:
    return load_builder_manifest(
        REPOSITORY_ROOT / "builder_manifest" / "product_builder_v0_10.yaml"
    )


def _builder_key(property_id: str, suffix: str = "value") -> str:
    safe_property = (
        property_id.replace(":", "_")
        .replace("/", "_")
        .replace("-", "_")
    )
    reset_index = st.session_state.get("manual_builder_reset_index", 0)
    return f"manual_builder_{reset_index}_{safe_property}_{suffix}"


def reset_manual_builder() -> None:
    for key in list(st.session_state):
        if key.startswith("manual_builder_") and key != "manual_builder_reset_index":
            st.session_state.pop(key, None)
    st.session_state["manual_builder_reset_index"] = (
        st.session_state.get("manual_builder_reset_index", 0) + 1
    )


def _property_metadata_index(dataset: object, manifest: dict) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for property_item in getattr(dataset, "properties", []):
        evidence = [
            asdict(item)
            for item in getattr(property_item, "evidence", [])
        ]
        index[property_item.term_id] = {
            "term_id": property_item.term_id,
            "label": property_item.label,
            "comment": property_item.comment,
            "domain": list(property_item.domain),
            "range": list(property_item.range),
            "sub_property_of": list(property_item.sub_property_of),
            "type": list(property_item.types),
            "term_status": property_item.term_status,
            "is_link_type": property_item.is_link_type,
            "coverage_status": property_item.coverage_status,
            "evidence": evidence,
            "supported_in_v0_10": True,
        }
    for group in manifest.get("groups", []):
        for field in group.get("properties", []):
            property_id = field.get("property_id")
            if not property_id:
                continue
            metadata = dict(index.get(property_id, {"term_id": property_id}))
            metadata.update(
                {
                    "requirement": field.get("requirement", "optional"),
                    "input_type_override": field.get("input_type_override"),
                    "example_value": field.get("example_value", ""),
                    "help_text": field.get("help_text", ""),
                    "appears_because": field.get("appears_because", ""),
                    "supported_in_v0_10": field.get("supported_in_v0_10", True),
                    "planned_reason": field.get("planned_reason", ""),
                }
            )
            index[property_id] = metadata
    return index


def _metadata_for_field(
    field: dict[str, Any],
    property_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    property_id = str(field["property_id"])
    metadata = dict(property_metadata.get(property_id, {"term_id": property_id}))
    metadata.update(
        {
            "requirement": field.get("requirement", "optional"),
            "input_type_override": field.get("input_type_override"),
            "example_value": field.get("example_value", ""),
            "help_text": field.get("help_text", ""),
            "appears_because": field.get("appears_because", ""),
            "supported_in_v0_10": field.get("supported_in_v0_10", True),
            "planned_reason": field.get("planned_reason", ""),
        }
    )
    return metadata


def _render_field_header(metadata: dict[str, Any]) -> None:
    property_id = metadata["term_id"]
    label = metadata.get("label") or property_id.split(":", 1)[-1]
    requirement = str(metadata.get("requirement") or "optional").title()
    ranges = ", ".join(metadata.get("range") or []) or "range unavailable"
    evidence = metadata.get("evidence") or []
    evidence_hint = (
        f"{len(evidence)} mapping evidence row(s)"
        if evidence
        else "No mapping catalog evidence linked"
    )
    st.markdown(f"**{label}**")
    st.caption(
        f"`{property_id}` | {requirement} | Range: {ranges} | {evidence_hint}"
    )
    if metadata.get("help_text"):
        st.caption(str(metadata["help_text"]))
    if metadata.get("example_value"):
        st.caption(f"Example: `{metadata['example_value']}`")


def _coerce_builder_widget_value(value: Any, input_type: str) -> Any:
    if input_type == "checkbox":
        return bool(value)
    if isinstance(value, str):
        return value.strip()
    return value


def _render_manual_field(
    state: dict[str, Any],
    metadata: dict[str, Any],
    *,
    default_language: str,
) -> dict[str, Any]:
    property_id = metadata["term_id"]
    input_type = infer_input_type(
        metadata,
        metadata.get("input_type_override"),
    )
    _render_field_header(metadata)
    if not metadata.get("supported_in_v0_10", True):
        st.info(
            "Planned for a later release: "
            + str(metadata.get("planned_reason") or "requires governed modelling")
        )
        return state

    key = _builder_key(property_id)
    if input_type == "language_text":
        value = st.text_input(
            f"{property_id} value",
            key=key,
            placeholder=str(metadata.get("example_value") or ""),
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(
                state,
                property_id,
                value,
                language=default_language,
            )
    elif input_type == "quantity":
        value_col, unit_col = st.columns([1, 0.7])
        value = value_col.text_input(
            f"{property_id} quantity value",
            key=key,
            placeholder="1.0",
            label_visibility="collapsed",
        )
        unit_code = unit_col.text_input(
            f"{property_id} unitCode",
            key=_builder_key(property_id, "unit"),
            placeholder="LTR",
            label_visibility="collapsed",
        )
        if value or unit_code:
            state = update_builder_value(
                state,
                property_id,
                value,
                unit_code=unit_code,
            )
    elif input_type == "checkbox":
        value = st.checkbox(
            f"{property_id} value",
            key=key,
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(state, property_id, value)
    elif input_type == "url":
        value = st.text_input(
            f"{property_id} URL",
            key=key,
            placeholder=str(metadata.get("example_value") or "https://"),
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(state, property_id, value)
    else:
        value = st.text_input(
            f"{property_id} value",
            key=key,
            placeholder=str(metadata.get("example_value") or ""),
            label_visibility="collapsed",
        )
        value = _coerce_builder_widget_value(value, input_type)
        if value not in ("", None):
            state = update_builder_value(state, property_id, value)
    return state


def _backlog_categories(backlog: list[dict]) -> list[str]:
    return sorted(
        {
            str(item["category"]).replace("_", " ")
            for item in backlog
            if item.get("category")
        }
    )


def _render_single_xml_workflow(mapping_path: Path) -> None:
    with st.container(border=True):
        render_section_header(
            1,
            "Upload product data",
            "Choose one XML product message. The source remains in memory and is "
            "not written to the repository.",
        )
        uploaded_file = st.file_uploader(
            "GDSN product XML",
            type=["xml"],
            help="Accepted format: one XML file. The file is processed in memory.",
        )

        if uploaded_file is None:
            render_empty_upload_state()
        elif st.button(
            "Convert product to JSON-LD",
            type="primary",
            use_container_width=True,
        ):
            clear_results()
            try:
                with st.spinner("Converting and validating product data..."):
                    result = convert_xml_to_jsonld(
                        uploaded_file.getvalue(),
                        mapping_path,
                        write_files=False,
                    )
            except (XMLParseError, FileNotFoundError, ValueError) as exc:
                st.error(f"Conversion failed: {exc}")
            else:
                output_name_base = result.canonical_product.gtin or "unknown"
                st.session_state["conversion_result"] = result
                st.session_state["jsonld_bytes"] = json_bytes(result.jsonld_data)
                st.session_state["mapping_report_bytes"] = mapping_report_xlsx_bytes(
                    result.mapping_report_rows
                )
                st.session_state["validation_report_bytes"] = json_bytes(
                    result.validation_report
                )
                st.session_state["unmapped_fields_bytes"] = json_bytes(
                    result.unmapped_fields
                )
                st.session_state["output_name_base"] = output_name_base

    result = st.session_state.get("conversion_result")
    if result is not None:
        with st.container(border=True):
            render_section_header(
                2,
                "Review conversion result",
                "Check validation first, then inspect the product identity and "
                "generated structured data.",
            )

            validation = result.validation_report
            if validation["valid"] and not validation["warnings"]:
                validation_tone = "success"
                validation_title = "Conversion complete"
                validation_detail = "Validation passed with no warnings."
                validation_value = "Passed"
            elif validation["valid"]:
                validation_tone = "warning"
                validation_title = "Conversion complete with review points"
                validation_detail = (
                    f"Validation passed with {len(validation['warnings'])} "
                    "warning(s)."
                )
                validation_value = "Passed with warnings"
            else:
                validation_tone = "error"
                validation_title = "Conversion complete with validation errors"
                validation_detail = (
                    f"Review {len(validation['errors'])} validation error(s) "
                    "before using the output."
                )
                validation_value = "Review required"

            mapped_rows = sum(
                1 for row in result.mapping_report_rows if row.get("found")
            )
            unmapped_rows = len(
                result.unmapped_fields.get("unmapped_elements", [])
            )
            render_result_summary(
                validation_value,
                validation_detail,
                mapped_rows,
                unmapped_rows,
            )

            status_column, identity_column = st.columns([1, 1.2])
            with status_column:
                render_status_card(
                    validation_tone,
                    validation_title,
                    validation_detail,
                )

            product_id = result.jsonld_data.get("@id")
            with identity_column:
                if product_id:
                    render_identity_card(product_id)

            render_preview_heading(
                "Generated JSON-LD",
                "Open the complete, copyable GS1 Web Vocabulary-aligned output.",
                "JSON-LD",
            )
            formatted_jsonld = json.dumps(
                result.jsonld_data,
                indent=2,
                ensure_ascii=False,
            )
            with st.expander("Open structured data preview"):
                st.code(formatted_jsonld, language="json")

        with st.container(border=True):
            render_section_header(
                3,
                "Inspect traceability and export",
                "Review the applied mappings and download the generated data and "
                "diagnostic reports.",
            )
            render_preview_heading(
                "Mapping report preview",
                "Compare source fields, canonical fields, and generated properties.",
                f"{mapped_rows}/{len(result.mapping_report_rows)} mapped",
            )
            with st.expander("Open mapping trace preview"):
                st.dataframe(
                    pd.DataFrame(result.mapping_report_rows),
                    use_container_width=True,
                )

            output_name_base = st.session_state["output_name_base"]
            render_preview_heading(
                "Export package",
                "Download the product output and all supporting review reports.",
                "4 files",
            )
            download_top_left, download_top_right = st.columns(2)
            with download_top_left:
                with st.container(border=True):
                    render_download_intro(
                        "Product JSON-LD",
                        "Machine-readable GS1 Web Vocabulary product data.",
                        "JSON-LD",
                    )
                    st.download_button(
                        "Download JSON-LD",
                        data=st.session_state["jsonld_bytes"],
                        file_name=f"product_{output_name_base}.jsonld",
                        mime="application/ld+json",
                        use_container_width=True,
                    )
            with download_top_right:
                with st.container(border=True):
                    render_download_intro(
                        "Mapping report XLSX",
                        "Excel trace of source fields and generated properties.",
                        "XLSX",
                    )
                    st.download_button(
                        "Download mapping report XLSX",
                        data=st.session_state["mapping_report_bytes"],
                        file_name=f"mapping_report_{output_name_base}.xlsx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        use_container_width=True,
                    )

            download_bottom_left, download_bottom_right = st.columns(2)
            with download_bottom_left:
                with st.container(border=True):
                    render_download_intro(
                        "Validation report JSON",
                        "JSON summary of errors, warnings, and validation status.",
                        "JSON",
                    )
                    st.download_button(
                        "Download validation report JSON",
                        data=st.session_state["validation_report_bytes"],
                        file_name=f"validation_report_{output_name_base}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            with download_bottom_right:
                with st.container(border=True):
                    render_download_intro(
                        "Unmapped fields JSON",
                        "JSON inventory of populated XML outside the profile.",
                        "JSON",
                    )
                    st.download_button(
                        "Download unmapped fields report JSON",
                        data=st.session_state["unmapped_fields_bytes"],
                        file_name=f"unmapped_fields_{output_name_base}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

            render_review_guidance()
            st.button(
                "Clear results",
                on_click=clear_results,
                use_container_width=True,
            )


def _render_bulk_zip_workflow(mapping_path: Path) -> None:
    with st.container(border=True):
        render_section_header(
            1,
            "Upload batch ZIP",
            "Upload a ZIP containing one or more GDSN XML product messages.",
        )
        st.info(
            "Only XML files in the ZIP are processed. Files are handled in memory "
            "where possible."
        )
        uploaded_zip = st.file_uploader(
            "GDSN XML batch ZIP",
            type=["zip"],
            key="bulk_zip_uploader",
            help="Non-XML files are ignored. XML files are converted independently.",
        )
        if uploaded_zip is not None and st.button(
            "Convert ZIP batch",
            type="primary",
            use_container_width=True,
        ):
            clear_batch_results()
            try:
                with st.spinner("Converting XML files from ZIP..."):
                    report = convert_batch_zip(
                        uploaded_zip.getvalue(),
                        mapping_path,
                        limits=BatchConversionLimits(),
                    )
            except BatchConversionError as exc:
                st.error(f"Batch conversion failed: {exc}")
            else:
                st.session_state["batch_conversion_report"] = report
                st.session_state["batch_export_zip_bytes"] = report.export_zip_bytes

    report = st.session_state.get("batch_conversion_report")
    if report is not None:
        summary = report.summary["summary"]
        with st.container(border=True):
            render_section_header(
                2,
                "Review batch results",
                "Check per-file status before downloading the complete batch package.",
            )
            first, second, third, fourth, fifth = st.columns(5)
            first.metric("XML files found", summary["xml_files_found"])
            second.metric("Successful conversions", summary["successful_conversions"])
            third.metric("Failed conversions", summary["failed_conversions"])
            fourth.metric("Total unmapped fields", summary["total_unmapped_fields"])
            fifth.metric(
                "Validation issues/warnings",
                summary["validation_error_count"]
                + summary["validation_warning_count"],
            )
            st.dataframe(
                pd.DataFrame(report.preview_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "Download batch export ZIP",
                data=st.session_state["batch_export_zip_bytes"],
                file_name="gdsn_batch_export.zip",
                mime="application/zip",
                use_container_width=True,
            )


def _render_webvoc_explorer() -> None:
    try:
        dataset = _load_webvoc_explorer_dataset()
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"Web Vocabulary Explorer could not load local sources: {exc}")
        return

    with st.container(border=True):
        render_section_header(
            1,
            "Explore GS1 Web Vocabulary",
            "Browse the local GS1 Web Vocabulary snapshot and compare vocabulary "
            "terms with GDSN mapping coverage.",
        )
        summary = dataset.summary
        metric_columns = st.columns(5)
        metric_columns[0].metric(
            "WebVoc version",
            summary.get("webvoc_version") or "unknown",
        )
        metric_columns[1].metric("Classes", summary["class_count"])
        metric_columns[2].metric("Properties", summary["property_count"])
        metric_columns[3].metric("Mapped properties", summary["mapped_property_count"])
        metric_columns[4].metric(
            "Standards review",
            summary["standards_review_property_count"],
        )
        with st.expander("Class reference"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Class": item.term_id,
                            "Label": item.label,
                            "Description": item.comment,
                            "subClassOf": ", ".join(item.sub_class_of),
                            "Status": item.term_status,
                        }
                        for item in dataset.classes
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )

    properties = list(dataset.properties)
    all_domains = sorted(
        {
            domain
            for property_item in properties
            for domain in property_item.domain
            if domain
        }
    )

    with st.container(border=True):
        render_section_header(
            2,
            "Filter vocabulary coverage",
            "Narrow by review group, domain, coverage status, and term text. "
            "The Explorer is read-only and does not write mappings.",
        )
        top_left, top_mid, top_right = st.columns([1.2, 1, 1])
        with top_left:
            selected_group = st.selectbox(
                "Group",
                ["All groups", *PROPERTY_GROUPS],
                help="Pragmatic grouping for GS1/GDSN mapping review.",
            )
        with top_mid:
            selected_domain = st.selectbox(
                "Domain",
                ["All domains", *all_domains],
                help="Optional Web Vocabulary domain/root selector.",
            )
        with top_right:
            selected_coverage = st.selectbox(
                "Coverage status",
                ["All statuses", *COVERAGE_STATUSES],
            )
        search = st.text_input(
            "Search properties",
            placeholder="Search property, label, comment, BMS field, or XPath evidence",
        )
        check_left, check_right = st.columns(2)
        with check_left:
            only_mapped = st.checkbox("Show only mapped")
        with check_right:
            only_standards_review = st.checkbox("Show only standards review")

    filtered_properties = filter_properties(
        properties,
        group=selected_group,
        coverage_status=selected_coverage,
        search=search,
        only_mapped=only_mapped,
        only_standards_review=only_standards_review,
    )
    if selected_domain != "All domains":
        filtered_properties = [
            item for item in filtered_properties if selected_domain in item.domain
        ]

    with st.container(border=True):
        render_section_header(
            3,
            "Review vocabulary properties",
            "Inspect local WebVoc terms with catalog coverage, BMS/XPath evidence, "
            "and SDR indicators.",
        )
        st.caption(
            f"{len(filtered_properties)} of {len(properties)} properties shown. "
            "Coverage comes from the local mapping catalog."
        )
        visible_columns = {
            "Group",
            "Property",
            "Label",
            "Domain",
            "Range",
            "Coverage",
            "BMS/XPath evidence",
            "SDR indicator",
        }
        table_rows = [
            {
                key: value
                for key, value in property_to_row(property_item).items()
                if key in visible_columns
            }
            for property_item in filtered_properties
        ]
        st.dataframe(
            pd.DataFrame(table_rows),
            hide_index=True,
            use_container_width=True,
        )

        if filtered_properties:
            selected_property_id = st.selectbox(
                "Selected property detail",
                [item.term_id for item in filtered_properties],
                format_func=lambda term: next(
                    (
                        f"{item.term_id} - {item.label}"
                        for item in filtered_properties
                        if item.term_id == term
                    ),
                    term,
                ),
            )
            selected_property = next(
                item
                for item in filtered_properties
                if item.term_id == selected_property_id
            )
            with st.expander("Property detail", expanded=True):
                detail_left, detail_right = st.columns([1.1, 1])
                with detail_left:
                    st.markdown("**Term**")
                    st.code(selected_property.term_id)
                    st.markdown("**Full IRI**")
                    st.code(selected_property.full_iri)
                    st.markdown("**Label**")
                    st.write(selected_property.label or "No label available")
                    st.markdown("**Description**")
                    st.write(selected_property.comment or "No description available")
                with detail_right:
                    st.markdown("**Domain / Range**")
                    st.write(", ".join(selected_property.domain) or "Not specified")
                    st.write(", ".join(selected_property.range) or "Not specified")
                    st.markdown("**subPropertyOf**")
                    st.write(
                        ", ".join(selected_property.sub_property_of)
                        or "Not specified"
                    )
                    st.markdown("**Coverage status**")
                    st.code(selected_property.coverage_status)
                    st.markdown("**Link type**")
                    st.write("Yes" if selected_property.is_link_type else "No")

                st.markdown("**GDSN mapping evidence**")
                if selected_property.evidence:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                asdict(evidence)
                                for evidence in selected_property.evidence
                            ]
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info("No mapping catalog evidence is linked to this property.")

                st.markdown("**SDR/governance notes**")
                if selected_property.governance:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                asdict(reference)
                                for reference in selected_property.governance
                            ]
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info("No open SDR reference is linked to this property.")

    with st.container(border=True):
        render_section_header(
            4,
            "Manual JSON-LD Builder",
            "Use the Create JSON-LD Prototype workflow to author range-aware "
            "manual product markup.",
        )
        st.info(
            "The Explorer remains read-only. Manual prototypes are entered in a "
            "separate workflow and are not GDSN/BMS/XPath traceable unless "
            "linked to governed mapping evidence."
        )


def _render_manual_jsonld_builder() -> None:
    try:
        dataset = _load_webvoc_explorer_dataset()
        manifest = _load_builder_manifest()
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"Manual JSON-LD Builder could not load local sources: {exc}")
        return

    property_metadata = _property_metadata_index(dataset, manifest)
    categories = [
        item["label"]
        for item in manifest.get("product_categories", [])
        if isinstance(item, dict) and item.get("label")
    ]
    root_classes = [
        item["label"]
        for item in manifest.get("root_classes", [])
        if isinstance(item, dict) and item.get("label")
    ]
    language_options = manifest.get("default_language_options", ["en", "nl", "de", "fr"])

    with st.container(border=True):
        render_section_header(
            1,
            "Create JSON-LD Prototype",
            "Manually select GS1 Web Vocabulary properties, enter values, and "
            "preview prototype JSON-LD live.",
        )
        st.warning(
            "Manual JSON-LD prototype. This output is entered manually, not "
            "generated from GDSN XML. It is not BMS/XPath traceable unless linked "
            "to governed mapping evidence. It is not an official GS1 validation "
            "result."
        )

    control_column, form_column, output_column = st.columns([0.86, 1.25, 1.05])
    with control_column:
        with st.container(border=True):
            render_section_header(
                2,
                "Builder controls",
                "Choose the root class, category, language, and thematic group.",
            )
            root_class = st.selectbox(
                "Root class",
                root_classes or ["Product"],
                help="v0.10 supports Product only.",
            )
            product_category = st.selectbox(
                "Product category",
                categories or ["General Product"],
                help="Controls which thematic groups are offered.",
            )
            default_language = st.selectbox(
                "Default language",
                language_options,
                help="Used for language-tagged Web Vocabulary values.",
            )
            st.checkbox(
                "Product is for sale",
                help=(
                    "Form helper only in v0.10. This does not emit unsupported "
                    "offer JSON-LD."
                ),
            )

            groups = get_builder_groups(manifest, product_category)
            group_labels = [group["label"] for group in groups]
            selected_group_label = st.selectbox(
                "Thematic group",
                group_labels,
                help="Select which manifest-driven field group to edit.",
            )
            selected_group = next(
                group for group in groups if group["label"] == selected_group_label
            )

    state = build_empty_builder_state(root_class=root_class)
    state["product_category"] = product_category
    state["default_language"] = default_language
    state["selected_groups"] = [selected_group["key"]]
    fields = get_builder_fields(manifest, selected_group)

    with form_column:
        with st.container(border=True):
            render_section_header(
                3,
                selected_group["label"],
                selected_group.get("description", "Enter values for this group."),
            )
            for field in fields:
                metadata = _metadata_for_field(field, property_metadata)
                with st.container(border=True):
                    state = _render_manual_field(
                        state,
                        metadata,
                        default_language=default_language,
                    )

    jsonld_data = serialize_builder_state_to_jsonld(state, property_metadata)
    warnings = validate_builder_state(state, property_metadata)
    state["validation_warnings"] = warnings

    with output_column:
        with st.container(border=True):
            render_section_header(
                4,
                "Generated JSON-LD Output",
                "Live preview of the current manual prototype.",
            )
            if warnings:
                for warning in warnings:
                    st.warning(warning)
            st.json(jsonld_data)
            formatted_jsonld = json.dumps(
                jsonld_data,
                indent=2,
                ensure_ascii=False,
            )
            st.code(formatted_jsonld, language="json")
            gtin = jsonld_data.get("gtin") or "manual-prototype"
            st.download_button(
                "Download JSON-LD",
                data=prototype_jsonld_bytes(jsonld_data),
                file_name=f"manual_jsonld_{gtin}.jsonld",
                mime="application/ld+json",
                use_container_width=True,
            )
            st.button(
                "Clear builder",
                on_click=reset_manual_builder,
                use_container_width=True,
            )


def _render_standards_review_mode(backlog: list[dict]) -> None:
    categories = _backlog_categories(backlog)
    with st.container(border=True):
        render_section_header(
            1,
            "Standards Review",
            "Read-only status for open standards and governance decisions.",
        )
        count_column, category_column = st.columns([1, 2])
        count_column.metric("Open SDRs", len(backlog))
        category_column.markdown(
            "**Categories**\n\n"
            + (", ".join(categories) if categories else "metadata unavailable")
        )
        st.markdown("**Register**")
        st.code("docs/standards-decisions/index.md")
        st.info(
            "These are standards/governance decisions, not runtime converter failures."
        )


def main() -> None:
    st.set_page_config(
        page_title="GDSN to GS1 JSON-LD Converter",
        page_icon="G",
        layout="wide",
    )
    apply_page_styles()
    render_page_header()
    render_workflow_overview()
    if st.session_state.get("workflow_mode") not in {
        mode["title"] for mode in WORKFLOW_MODES
    }:
        st.session_state["workflow_mode"] = DEFAULT_WORKFLOW_MODE

    mapping_profiles = {
        "Certifications & Documents v0.3.0": (
            REPOSITORY_ROOT / "mapping" / "mapping_v0_3.yaml"
        ),
        "Food v0.2.0 mapping": REPOSITORY_ROOT / "mapping" / "mapping_v0_2.yaml",
        "MVP v0.1.0 mapping": REPOSITORY_ROOT / "mapping" / "mapping_mvp.yaml",
    }

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
              <strong>Conversion workspace</strong>
              <span>App version: {APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(
                '<p class="sidebar-label">Conversion settings</p>',
                unsafe_allow_html=True,
            )
            selected_profile = st.selectbox(
                "Mapping profile",
                list(mapping_profiles),
                on_change=clear_all_results,
                help="Changing the profile clears current conversion results.",
            )
            mapping_path = mapping_profiles[selected_profile]
            st.markdown("**Active mapping file**")
            st.code(mapping_path.relative_to(REPOSITORY_ROOT).as_posix())

        with st.expander("Profile coverage", expanded=True):
            st.markdown(
                """
    <p class="sidebar-label">Supported groups</p>
    <div class="coverage-badges">
      <span class="coverage-badge">Identity</span>
      <span class="coverage-badge">Descriptions</span>
      <span class="coverage-badge">Brand &amp; GPC</span>
      <span class="coverage-badge">Net content</span>
      <span class="coverage-badge">Images &amp; links</span>
      <span class="coverage-badge">Ingredients</span>
      <span class="coverage-badge">Allergens</span>
      <span class="coverage-badge">Nutrients</span>
      <span class="coverage-badge">Certifications</span>
      <span class="coverage-badge">Documents</span>
    </div>
    """,
                unsafe_allow_html=True,
            )

        webvoc_metadata = _load_webvoc_metadata()
        render_vocabulary_status(
            webvoc_metadata.get("detected_version"),
            webvoc_metadata.get("detected_last_modified"),
        )

        backlog = _load_open_standards_backlog()
        render_standards_backlog_status(
            len(backlog),
            _backlog_categories(backlog),
        )

    with st.container(border=True):
        render_workflow_entry_intro()
        workflow_columns = st.columns(len(WORKFLOW_MODES))
        for column, mode in zip(workflow_columns, WORKFLOW_MODES, strict=True):
            with column:
                selected = st.session_state["workflow_mode"] == mode["title"]
                render_workflow_mode_card(
                    mode["title"],
                    mode["description"],
                    mode["outcome"],
                    mode["marker"],
                    selected,
                )
                st.button(
                    "Active" if selected else "Open",
                    key=f"workflow_mode_{mode['key']}",
                    type="primary" if selected else "secondary",
                    disabled=selected,
                    on_click=set_workflow_mode,
                    args=(mode["title"],),
                    use_container_width=True,
                )

    workflow_mode = st.session_state["workflow_mode"]
    if workflow_mode == "Convert GDSN XML":
        single_tab, bulk_tab = st.tabs(["Single XML", "Bulk ZIP"])
        with single_tab:
            _render_single_xml_workflow(mapping_path)
        with bulk_tab:
            _render_bulk_zip_workflow(mapping_path)
    elif workflow_mode == "Explore GS1 Web Vocabulary":
        _render_webvoc_explorer()
    elif workflow_mode == "Create JSON-LD Prototype":
        _render_manual_jsonld_builder()
    else:
        _render_standards_review_mode(backlog)


if __name__ == "__main__":
    main()
