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
    object_subfield_key,
    serialize_builder_state_to_jsonld,
    update_builder_value,
    validate_builder_state,
)
from gdsn_to_gs1_jsonld.mapping_candidate_generator import (
    build_candidate_inputs,
    candidate_report_bytes_csv,
    candidate_report_bytes_json,
    candidate_report_bytes_xlsx,
    filter_candidates,
    generate_all_candidates,
    generate_candidates_for_property,
    generate_candidate_summary,
)
from gdsn_to_gs1_jsonld.product_passport_sources import (
    build_product_passport_source_inventory,
    inventory_report_bytes_csv,
    inventory_report_bytes_json,
    load_product_passport_source_manifest,
    validate_product_passport_source_manifest,
    validate_product_passport_json,
    load_json_schema,
)
from gdsn_to_gs1_jsonld.product_passport_builder import (
    DEFAULT_SCHEMA_PATH as PP_BUILDER_DEFAULT_SCHEMA,
    build_minimal_product_passport,
    build_product_passport_summary,
    extract_brand,
    extract_gtin,
    extract_product_identifier,
    extract_product_name,
    normalize_gs1_jsonld_input,
    product_passport_report_bytes_json,
    product_passport_to_json_bytes,
    validate_built_product_passport,
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
    render_convert_progress,
    render_route_card,
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
        "description": "Convert product XML into GS1 Web Vocabulary JSON-LD.",
        "outcome": "JSON-LD + mapping, validation, and unmapped-field evidence.",
    },
    {
        "key": "explore",
        "title": "Explore GS1 Web Vocabulary",
        "marker": "VOC",
        "description": "Browse local GS1 vocabulary classes and properties.",
        "outcome": "Vocabulary evidence and coverage context (read-only).",
    },
    {
        "key": "candidates",
        "title": "Generate Mapping Candidates",
        "marker": "MAP",
        "description": (
            "Suggest possible GDSN/BMS/XPath sources for WebVoc properties."
        ),
        "outcome": "Review-only candidate report; nothing is written.",
    },
    {
        "key": "standards",
        "title": "Standards Review",
        "marker": "SDR",
        "description": "Inspect open standards and governance decisions.",
        "outcome": "Read-only SDR context.",
    },
    {
        "key": "prototype",
        "title": "Create JSON-LD Prototype",
        "marker": "LD",
        "description": "Manually author GS1 Web Vocabulary JSON-LD.",
        "outcome": "Prototype JSON-LD with governance warning.",
    },
    {
        "key": "product_passport",
        "title": "Validate Product Passport Sources",
        "marker": "PP",
        "description": (
            "Inspect local Product Passport reference sources, schemas, and "
            "examples."
        ),
        "outcome": "Source inventory + structural validation report.",
    },
    {
        "key": "product_passport_builder",
        "title": "Build Product Passport Prototype",
        "marker": "PB",
        "description": (
            "Wrap GS1 JSON-LD into a prototype Product Passport envelope."
        ),
        "outcome": "Passport JSON-LD + structural validation report.",
    },
)
DEFAULT_WORKFLOW_MODE = WORKFLOW_MODES[0]["title"]

# Information-architecture grouping for the workflow overview (v0.13.0).
# Cards are rendered under these group headings, in this order, so seven
# Guided route navigation (v0.13.3): three primary routes group the seven
# workflows. Stage 1 shows the route cards; stage 2 shows only the child
# workflow cards for the selected route (progressive disclosure). The routes are
# a UI grouping layer only — every workflow key is unchanged and reachable.
ROUTES = (
    {
        "key": "jsonld_creation",
        "title": "Create GS1 JSON-LD",
        "marker": "JSON-LD",
        "description": (
            "Create GS1 Web Vocabulary JSON-LD from product XML or manual "
            "prototype input."
        ),
        "outcome": "GS1 JSON-LD output.",
        "children": ("convert", "prototype"),
        "child_heading": "Choose how to create JSON-LD",
    },
    {
        "key": "vocabulary_mapping",
        "title": "Vocabulary & Mapping",
        "marker": "MAP",
        "description": (
            "Review vocabulary, mappings, candidate sources and standards "
            "decisions."
        ),
        "outcome": "Review evidence and governance context.",
        "children": ("explore", "candidates", "standards"),
        "child_heading": "Choose a review tool",
    },
    {
        "key": "product_passport_bridge",
        "title": "Product Passport Bridge",
        "marker": "PASS",
        "description": (
            "Work with Product Passport sources and prototype passport output."
        ),
        "outcome": "Source validation or Passport JSON-LD.",
        "children": ("product_passport", "product_passport_builder"),
        "child_heading": "Choose a Product Passport tool",
    },
)
DEFAULT_ROUTE = ROUTES[0]["key"]


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


def set_route(route_key: str) -> None:
    """Select a primary route and open its first child workflow.

    This is a UI navigation grouping only. It changes which child workflow cards
    are shown and makes the route's first child the active workflow, without
    clearing any conversion or result state.
    """
    st.session_state["selected_route"] = route_key
    for route in ROUTES:
        if route["key"] == route_key:
            first_child_key = route["children"][0]
            for mode in WORKFLOW_MODES:
                if mode["key"] == first_child_key:
                    st.session_state["workflow_mode"] = mode["title"]
                    return
            return


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
    st.session_state.pop("manual_builder_values", None)
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
                    "object_type": field.get("object_type"),
                    "object_fields": field.get("object_fields"),
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
        else "No catalog evidence linked"
    )
    st.markdown(f"**{label}** — {requirement}")
    st.caption(f"`{property_id}` · Range: {ranges} · {evidence_hint}")
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


def _render_field_widget(
    state: dict[str, Any],
    state_id: str,
    input_type: str,
    metadata: dict[str, Any],
    *,
    default_language: str,
) -> dict[str, Any]:
    """Render a single builder input for *state_id* and update state.

    Used for both top-level fields and nested-object sub-fields; the state key
    for a sub-field is the ``parent#child`` compound id.
    """
    key = _builder_key(state_id)
    if input_type == "language_text":
        value = st.text_input(
            f"{state_id} value",
            key=key,
            placeholder=str(metadata.get("example_value") or ""),
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(
                state, state_id, value, language=default_language
            )
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "quantity":
        value_col, unit_col = st.columns([1, 0.7])
        value = value_col.text_input(
            f"{state_id} quantity value",
            key=key,
            placeholder="1.0",
            label_visibility="collapsed",
        )
        unit_code = unit_col.text_input(
            f"{state_id} unitCode",
            key=_builder_key(state_id, "unit"),
            placeholder="LTR",
            label_visibility="collapsed",
        )
        if value or unit_code:
            state = update_builder_value(state, state_id, value, unit_code=unit_code)
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "checkbox":
        value = st.checkbox(
            f"{state_id} value",
            key=key,
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(state, state_id, value)
        else:
            state = update_builder_value(state, state_id, "")
    elif input_type == "url":
        value = st.text_input(
            f"{state_id} URL",
            key=key,
            placeholder=str(metadata.get("example_value") or "https://"),
            label_visibility="collapsed",
        )
        if value:
            state = update_builder_value(state, state_id, value)
        else:
            state = update_builder_value(state, state_id, "")
    else:
        value = st.text_input(
            f"{state_id} value",
            key=key,
            placeholder=str(metadata.get("example_value") or ""),
            label_visibility="collapsed",
        )
        value = _coerce_builder_widget_value(value, input_type)
        if value not in ("", None):
            state = update_builder_value(state, state_id, value)
        else:
            state = update_builder_value(state, state_id, "")
    return state


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

    if input_type == "object":
        object_fields = metadata.get("object_fields") or []
        if not object_fields:
            st.info("This object has no simple sub-fields available to author.")
            return state
        object_type = metadata.get("object_type") or "object"
        st.caption(
            f"Nested {object_type} object — fill any sub-field to include it in "
            "the prototype."
        )
        for sub in object_fields:
            sub_id = sub.get("property_id")
            if not sub_id:
                continue
            sub_type = sub.get("input_type_override") or sub.get("input_type") or "text"
            compound_id = object_subfield_key(property_id, sub_id)
            help_text = sub.get("help_text") or ""
            st.markdown(f"**{sub_id}**" + (f" — {help_text}" if help_text else ""))
            state = _render_field_widget(
                state,
                compound_id,
                sub_type,
                sub,
                default_language=default_language,
            )
        return state

    return _render_field_widget(
        state,
        property_id,
        input_type,
        metadata,
        default_language=default_language,
    )


def _backlog_categories(backlog: list[dict]) -> list[str]:
    return sorted(
        {
            str(item["category"]).replace("_", " ")
            for item in backlog
            if item.get("category")
        }
    )


def _render_single_xml_workflow(mapping_path: Path) -> None:
    # Guided four-step conversion flow (Upload -> Mapping -> Validate -> Export)
    # wrapped around the real converter. The progress indicator is a visual
    # roadmap only; conversion behaviour, outputs, and warnings are unchanged.
    result = st.session_state.get("conversion_result")
    render_convert_progress(converted=result is not None)

    # Step 1 — Upload GDSN XML
    with st.container(border=True):
        render_section_header(
            1,
            "Upload GDSN XML",
            "Choose one XML product message. The source stays in memory and is "
            f"not written to the repository. Active mapping profile: "
            f"{mapping_path.stem}.",
        )
        uploaded_file = st.file_uploader(
            "GDSN product XML",
            type=["xml"],
            help="Accepted format: one XML file. The file is processed in memory.",
        )

        if uploaded_file is None and result is None:
            render_empty_upload_state()
        if uploaded_file is not None and st.button(
            "Convert product to JSON-LD",
            type="primary",
            use_container_width=True,
        ):
            clear_results()
            try:
                with st.spinner("Converting and validating product data..."):
                    conversion = convert_xml_to_jsonld(
                        uploaded_file.getvalue(),
                        mapping_path,
                        write_files=False,
                    )
            except (XMLParseError, FileNotFoundError, ValueError) as exc:
                st.error(f"Conversion failed: {exc}")
            else:
                output_name_base = conversion.canonical_product.gtin or "unknown"
                st.session_state["conversion_result"] = conversion
                st.session_state["jsonld_bytes"] = json_bytes(conversion.jsonld_data)
                st.session_state["mapping_report_bytes"] = mapping_report_xlsx_bytes(
                    conversion.mapping_report_rows
                )
                st.session_state["validation_report_bytes"] = json_bytes(
                    conversion.validation_report
                )
                st.session_state["unmapped_fields_bytes"] = json_bytes(
                    conversion.unmapped_fields
                )
                st.session_state["output_name_base"] = output_name_base
                result = conversion

    if result is not None:
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
        output_name_base = st.session_state["output_name_base"]

        # Step 2 — Review mapping & evidence
        with st.container(border=True):
            render_section_header(
                2,
                "Review mapping & evidence",
                "Inspect the applied mapping profile and the source-to-property "
                "trace before using the output.",
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

        # Step 3 — Generate & validate output
        with st.container(border=True):
            render_section_header(
                3,
                "Generate & validate output",
                "Check validation first, then inspect the product identity and "
                "generated structured data.",
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

        # Step 4 — Export & actions
        with st.container(border=True):
            render_section_header(
                4,
                "Export & actions",
                "Download the generated data and diagnostic reports, or start "
                "over.",
            )
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
            "preview prototype JSON-LD live. This is a review and authoring tool, "
            "not a GDSN XML converter.",
        )
        st.warning(
            "⚠️ Prototype output only. "
            "This JSON-LD is entered manually, not generated from GDSN XML. "
            "It is not BMS/XPath traceable unless separately linked to governed "
            "mapping evidence. It is not an official GS1 validation result."
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
                "Product is for sale (form helper only — no JSON-LD emitted)",
                help=(
                    "This is a form-scoping helper only. v0.10 does not emit "
                    "offer or pricing JSON-LD for this flag."
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
    state["values"] = dict(st.session_state.get("manual_builder_values", {}))
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
    st.session_state["manual_builder_values"] = dict(state["values"])

    with output_column:
        with st.container(border=True):
            render_section_header(
                4,
                "Prototype JSON-LD Preview",
                "Live preview of the manually entered prototype. "
                "This is not converter output.",
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
                "Download prototype JSON-LD",
                data=prototype_jsonld_bytes(jsonld_data),
                file_name=f"manual_jsonld_prototype_{gtin}.jsonld",
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


@st.cache_data(show_spinner=False)
def _load_candidate_inputs() -> object:
    """Load and index all candidate generation inputs (cached)."""
    return build_candidate_inputs(
        webvoc_path=str(
            REPOSITORY_ROOT / "reference_data" / "normalized" / "webvoc_properties_1_17.csv"
        ),
        gdsn_path=str(
            REPOSITORY_ROOT
            / "reference_data"
            / "normalized"
            / "gdsn_attributes_bms_xpath_3_1_36.csv"
        ),
        catalog_path=str(
            REPOSITORY_ROOT
            / "mapping_catalog"
            / "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
        ),
        mapping_path=str(
            REPOSITORY_ROOT / "mapping" / "mapping_v0_3.yaml"
        ),
        backlog_path=str(
            REPOSITORY_ROOT
            / "docs"
            / "standards-decisions"
            / "standards_review_backlog.json"
        ),
    )


def _render_mapping_candidates_workflow() -> None:
    """Render the Generate Mapping Candidates workflow page."""
    with st.container(border=True):
        render_section_header(
            1,
            "Generate Mapping Candidates",
            "Propose possible GDSN/BMS/XPath source fields for GS1 Web Vocabulary "
            "properties. Candidates are review support only.",
        )
        st.warning(
            "Review support only. Candidates are proposals, not accepted mappings. "
            "They do not update mapping YAML, the mapping catalog, or converter "
            "behavior. Review each candidate before any mapping decision is made."
        )

    try:
        inputs = _load_candidate_inputs()
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.error(
            f"Mapping Candidate Generator could not load local reference data: {exc}"
        )
        return

    webvoc_ids = sorted(
        str(row.get("term_id") or "").strip()
        for row in inputs["webvoc_rows"]
        if row.get("term_id")
    )

    with st.container(border=True):
        render_section_header(
            2,
            "Controls",
            "Select a property or generate candidates for all properties.",
        )
        all_props_option = "All properties"
        property_options = [all_props_option] + webvoc_ids
        selected_property = st.selectbox(
            "WebVoc property",
            property_options,
            help="Select a specific property or 'All properties'.",
        )
        confidence_options = ["high", "medium", "low", "review_required"]
        selected_confidence = st.multiselect(
            "Confidence levels to include",
            confidence_options,
            default=["high", "medium", "low"],
            help="Filter candidates by confidence level.",
        )
        review_status_options = ["proposed", "already_mapped", "review_required", "not_recommended"]
        selected_review_statuses = st.multiselect(
            "Review statuses to include",
            review_status_options,
            default=["proposed", "already_mapped", "review_required"],
            help="Filter candidates by review status.",
        )
        include_already_mapped = st.checkbox(
            "Include already mapped",
            value=True,
            help="Include candidates where this property is already in the mapping catalog.",
        )
        include_low_conf = st.checkbox(
            "Include low confidence",
            value=True,
            help="Include candidates scored below medium confidence threshold.",
        )
        limit_per_prop = st.number_input(
            "Limit per property",
            min_value=1,
            max_value=50,
            value=20,
            step=1,
            help="Maximum candidate GDSN attributes per WebVoc property.",
        )
        generate_button = st.button(
            "Generate Candidates",
            type="primary",
            use_container_width=True,
        )

    if generate_button:
        with st.spinner("Generating mapping candidates..."):
            if selected_property == all_props_option:
                raw_candidates = generate_all_candidates(
                    inputs, limit_per_property=int(limit_per_prop)
                )
            else:
                raw_candidates = generate_candidates_for_property(
                    selected_property, inputs, limit=int(limit_per_prop)
                )

            # Apply confidence filter.
            min_conf = "high"
            if "low" in selected_confidence:
                min_conf = "low"
            elif "medium" in selected_confidence:
                min_conf = "medium"

            candidates = filter_candidates(
                raw_candidates,
                min_confidence=min_conf,
                include_low_confidence=include_low_conf,
                include_review_required="review_required" in selected_confidence,
            )
            # Apply review status filter.
            if selected_review_statuses:
                if not include_already_mapped:
                    selected_review_statuses = [
                        s for s in selected_review_statuses if s != "already_mapped"
                    ]
                candidates = [
                    c for c in candidates
                    if c.get("review_status") in selected_review_statuses
                ]

            st.session_state["candidate_results"] = candidates
            st.session_state["candidate_json_bytes"] = candidate_report_bytes_json(candidates)
            st.session_state["candidate_csv_bytes"] = candidate_report_bytes_csv(candidates)
            xlsx_b = candidate_report_bytes_xlsx(candidates)
            if xlsx_b:
                st.session_state["candidate_xlsx_bytes"] = xlsx_b

    candidates_result = st.session_state.get("candidate_results")
    if candidates_result is not None:
        summary = generate_candidate_summary(candidates_result)
        with st.container(border=True):
            render_section_header(
                3,
                "Candidate Metrics",
                "Review-only counts. No mappings are created or applied.",
            )
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Total candidates", summary["total_candidates"])
            m2.metric("High confidence", summary["by_confidence"].get("high", 0))
            m3.metric("Medium confidence", summary["by_confidence"].get("medium", 0))
            m4.metric("Low confidence", summary["by_confidence"].get("low", 0))
            m5.metric("Review required", summary["by_confidence"].get("review_required", 0))
            m6.metric("Already mapped", summary["by_review_status"].get("already_mapped", 0))

        with st.container(border=True):
            render_section_header(
                4,
                "Candidate Table",
                "Review candidates before any mapping decision. "
                "This table does not accept or write any mapping.",
            )
            if candidates_result:
                import pandas as pd

                table_rows = [
                    {
                        "WebVoc property": c.get("webvoc_property_id", ""),
                        "GDSN attribute name": c.get("gdsn_attribute_name", ""),
                        "BMS ID": c.get("gdsn_bms_id", ""),
                        "Score": c.get("score", 0.0),
                        "Confidence": c.get("confidence_level", ""),
                        "Review status": c.get("review_status", ""),
                        "Top reason": (c.get("reasons") or [""])[0],
                        "SDR linked": "; ".join(str(s) for s in (c.get("linked_sdr_ids") or [])),
                    }
                    for c in candidates_result
                ]
                df = pd.DataFrame(table_rows)
                st.dataframe(df, hide_index=True, use_container_width=True)

                if candidates_result:
                    selected_idx = st.selectbox(
                        "Select candidate for detail",
                        range(len(candidates_result)),
                        format_func=lambda i: (
                            f"{candidates_result[i].get('webvoc_property_id', '')} / "
                            f"{candidates_result[i].get('gdsn_attribute_name', '')} "
                            f"(score={candidates_result[i].get('score', 0):.3f})"
                        ),
                    )
                    with st.expander("Candidate detail", expanded=False):
                        selected_cand = candidates_result[selected_idx]
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("**WebVoc property**")
                            st.code(selected_cand.get("webvoc_property_id", ""))
                            st.markdown("**Label**")
                            st.write(selected_cand.get("webvoc_label") or "—")
                            st.markdown("**Comment**")
                            st.write(selected_cand.get("webvoc_comment") or "—")
                            st.markdown("**Domain / Range**")
                            st.write(
                                f"{selected_cand.get('webvoc_domain') or '—'} / "
                                f"{selected_cand.get('webvoc_range') or '—'}"
                            )
                        with col_b:
                            st.markdown("**GDSN attribute name**")
                            st.code(selected_cand.get("gdsn_attribute_name", ""))
                            st.markdown("**BMS ID / Module**")
                            st.write(
                                f"{selected_cand.get('gdsn_bms_id') or '—'} / "
                                f"{selected_cand.get('gdsn_module') or '—'}"
                            )
                            st.markdown("**DataType / Multiplicity**")
                            st.write(
                                f"{selected_cand.get('gdsn_data_type') or '—'} / "
                                f"{selected_cand.get('gdsn_multiplicity') or '—'}"
                            )
                            st.markdown("**Definition**")
                            st.write(selected_cand.get("gdsn_definition") or "—")
                        st.markdown("**Score / Confidence / Review status**")
                        st.write(
                            f"{selected_cand.get('score', 0):.4f} / "
                            f"{selected_cand.get('confidence_level', '—')} / "
                            f"{selected_cand.get('review_status', '—')}"
                        )
                        st.markdown("**Reasons**")
                        st.write("; ".join(selected_cand.get("reasons") or []) or "—")
                        st.markdown("**Warnings**")
                        st.write("; ".join(selected_cand.get("warnings") or []) or "None")
                        st.markdown("**Blocking notes**")
                        st.write(
                            "; ".join(selected_cand.get("blocking_notes") or []) or "None"
                        )
                        st.markdown("**Linked SDRs**")
                        st.write(
                            "; ".join(
                                str(s) for s in (selected_cand.get("linked_sdr_ids") or [])
                            ) or "None"
                        )
            else:
                st.info("No candidates match the selected filters.")

        with st.container(border=True):
            render_section_header(
                5,
                "Download Reports",
                "Download the candidate report for offline review. "
                "These reports do not modify any mapping file.",
            )
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            with dl_col1:
                with st.container(border=True):
                    render_download_intro(
                        "Candidate report JSON",
                        "Full candidate list with scores, reasons, and field metadata.",
                        "JSON",
                    )
                    json_bytes_data = st.session_state.get("candidate_json_bytes", b"")
                    st.download_button(
                        "Download mapping candidate report JSON",
                        data=json_bytes_data,
                        file_name="mapping_candidates.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            with dl_col2:
                with st.container(border=True):
                    render_download_intro(
                        "Candidate report CSV",
                        "Flat CSV for spreadsheet review and sorting.",
                        "CSV",
                    )
                    csv_bytes_data = st.session_state.get("candidate_csv_bytes", b"")
                    st.download_button(
                        "Download mapping candidate report CSV",
                        data=csv_bytes_data,
                        file_name="mapping_candidates.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            with dl_col3:
                with st.container(border=True):
                    render_download_intro(
                        "Candidate report XLSX",
                        "Excel workbook for review and annotation.",
                        "XLSX",
                    )
                    xlsx_bytes_data = st.session_state.get("candidate_xlsx_bytes", b"")
                    if xlsx_bytes_data:
                        st.download_button(
                            "Download mapping candidate report XLSX",
                            data=xlsx_bytes_data,
                            file_name="mapping_candidates.xlsx",
                            mime=(
                                "application/vnd.openxmlformats-officedocument"
                                ".spreadsheetml.sheet"
                            ),
                            use_container_width=True,
                        )
                    else:
                        st.info("XLSX generation requires openpyxl.")


def _render_validate_product_passport_workflow() -> None:
    """Render the Validate Product Passport Sources workflow page."""
    st.markdown(
        """
        <div class="pp-prototype-warning">
          <strong>Prototype / Reference only — not official GS1 validation</strong>
          v0.12.0 performs source inventory and structural JSON Schema validation only.
          It does not claim official GS1 validation, EU DPP regulatory compliance,
          or production readiness.
        </div>
        """,
        unsafe_allow_html=True,
    )

    manifest_path = REPOSITORY_ROOT / "product_passport" / "reference_sources" / "source_manifest.json"

    tab_inventory, tab_validator, tab_examples = st.tabs([
        "Source Inventory",
        "Schema Validator",
        "Examples",
    ])

    with tab_inventory:
        with st.container(border=True):
            render_section_header(
                1,
                "Product Passport Reference Source Inventory",
                "Load the source manifest and inspect all reference sources by type "
                "and sector. No files are fetched from the internet.",
            )
            st.info(
                "Prototype/reference only. Source inventory is structural metadata "
                "tracking only. No official GS1 validation or production compliance claimed."
            )

        if st.button("Load Source Manifest", type="primary", use_container_width=True):
            try:
                pp_manifest = load_product_passport_source_manifest(str(manifest_path))
                manifest_schema = None
                schema_sibling = manifest_path.parent / "source_manifest.schema.json"
                if schema_sibling.is_file():
                    try:
                        manifest_schema = load_json_schema(str(schema_sibling))
                    except (OSError, ValueError):
                        manifest_schema = None
                errors = validate_product_passport_source_manifest(
                    pp_manifest, schema=manifest_schema
                )
                base_dir = str(REPOSITORY_ROOT)
                inventory = build_product_passport_source_inventory(pp_manifest, base_dir=base_dir)
                st.session_state["pp_inventory"] = inventory
                st.session_state["pp_manifest_errors"] = errors
            except (FileNotFoundError, OSError, ValueError, Exception) as exc:
                st.error(f"Failed to load source manifest: {exc}")

        inventory = st.session_state.get("pp_inventory")
        manifest_errors = st.session_state.get("pp_manifest_errors", [])

        if manifest_errors:
            for err in manifest_errors:
                st.warning(f"Manifest issue: {err}")

        if inventory is None:
            st.markdown(
                """
                <div class="empty-state">
                  <span class="empty-state-mark" aria-hidden="true">PP</span>
                  <div>
                    <strong>Ready to load source manifest</strong>
                    <span>Click "Load Source Manifest" to inspect all reference sources by type and sector.</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if inventory is not None:
            with st.container(border=True):
                render_section_header(
                    2,
                    "Inventory Summary",
                    "Source counts by type and sector. Missing local files are placeholder entries that require a separate download.",
                )
                col_total, col_missing = st.columns(2)
                col_total.metric("Total sources", inventory.get("total_sources", 0))
                col_missing.metric(
                    "Missing local files",
                    len(inventory.get("missing_local_files", [])),
                )
                by_type = inventory.get("sources_by_type", {})
                by_sector = inventory.get("sources_by_sector", {})
                type_col, sector_col = st.columns(2)
                with type_col:
                    st.markdown("**By type**")
                    for k, v in sorted(by_type.items()):
                        st.write(f"{k}: {v}")
                with sector_col:
                    st.markdown("**By sector**")
                    for k, v in sorted(by_sector.items()):
                        st.write(f"{k}: {v}")

            with st.container(border=True):
                render_section_header(
                    3,
                    "Source Table",
                    "All source entries with file and checksum status.",
                )
                entries = inventory.get("entries", [])
                if entries:
                    table_rows = [
                        {
                            "source_id": e.get("source_id", ""),
                            "title": e.get("title", ""),
                            "source_type": e.get("source_type", ""),
                            "sector": e.get("sector", ""),
                            "version": e.get("version", ""),
                            "local_path": e.get("local_path", ""),
                            "file_exists": e.get("_file_exists", False),
                            "checksum_status": e.get("_checksum_status", ""),
                        }
                        for e in entries
                    ]
                    st.dataframe(
                        pd.DataFrame(table_rows),
                        hide_index=True,
                        use_container_width=True,
                    )

            with st.container(border=True):
                render_section_header(
                    4,
                    "Download Inventory",
                    "Download inventory reports for offline review.",
                )
                dl_inv_col, dl_csv_col = st.columns(2)
                with dl_inv_col:
                    render_download_intro(
                        "Inventory JSON",
                        "Full source inventory with checksum status.",
                        "JSON",
                    )
                    st.download_button(
                        "Download inventory JSON",
                        data=inventory_report_bytes_json(inventory),
                        file_name="product_passport_source_inventory.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                with dl_csv_col:
                    render_download_intro(
                        "Inventory CSV",
                        "Source table for spreadsheet review.",
                        "CSV",
                    )
                    st.download_button(
                        "Download inventory CSV",
                        data=inventory_report_bytes_csv(inventory),
                        file_name="product_passport_source_inventory.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

    with tab_validator:
        with st.container(border=True):
            render_section_header(
                1,
                "Schema Validator",
                "Validate a Product Passport JSON file against a local JSON Schema. "
                "Structural validation only.",
            )
            st.warning(
                "Structural validation only. Not official GS1 validation. "
                "Not production compliance."
            )

        # Load manifest to get schema list.
        pp_manifest_data: dict | None = None
        try:
            pp_manifest_data = load_product_passport_source_manifest(str(manifest_path))
        except (FileNotFoundError, OSError, Exception):
            pass

        schema_entries = []
        if pp_manifest_data:
            schema_entries = [
                s for s in pp_manifest_data.get("sources", [])
                if s.get("source_type") == "json_schema"
            ]

        # Only schemas whose local file exists are offered as active choices.
        # Placeholder schemas (file not yet downloaded) are listed as
        # unavailable rather than presented as selectable validation targets.
        local_schema_options: dict[str, str] = {}
        unavailable_schemas: list[str] = []
        for s in schema_entries:
            local_path = s.get("local_path", "")
            schema_file_candidate = REPOSITORY_ROOT / local_path if local_path else None
            label = f"{s.get('source_id')} — {s.get('title', '')}"
            if schema_file_candidate and schema_file_candidate.is_file():
                local_schema_options[label] = local_path
            else:
                unavailable_schemas.append(str(s.get("source_id", "")))

        # Always add the built-in minimal schema (committed, always available).
        minimal_schema_path = str(
            REPOSITORY_ROOT / "product_passport" / "reference_sources" / "raw_public" / "schemas" / "dpp_minimal.schema.json"
        )
        local_schema_options["dpp_minimal — Minimal DPP Structural Schema (built-in)"] = minimal_schema_path

        if unavailable_schemas:
            st.caption(
                "Unavailable — placeholder source file not downloaded yet: "
                + ", ".join(unavailable_schemas)
                + ". These remain listed in Source Inventory as provenance "
                "placeholders and cannot be used for validation until downloaded."
            )

        with st.container(border=True):
            render_section_header(
                2,
                "Input",
                "Upload a Product Passport JSON file or paste JSON text.",
            )
            input_mode = st.radio(
                "Input mode",
                ["Upload file", "Paste JSON"],
                horizontal=True,
            )

            instance_data: dict | None = None
            if input_mode == "Upload file":
                uploaded = st.file_uploader(
                    "Product Passport JSON file",
                    type=["json"],
                    help="Upload a JSON or JSON-LD file for structural validation.",
                )
                if uploaded is not None:
                    try:
                        instance_data = json.loads(uploaded.getvalue().decode("utf-8"))
                        st.success(f"Loaded: {uploaded.name}")
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        st.error(f"Could not parse JSON: {exc}")
            else:
                pasted = st.text_area(
                    "Paste Product Passport JSON",
                    height=200,
                    placeholder='{\n  "@context": "https://gs1.org/voc/",\n  "@type": "gs1:Product"\n}',
                )
                if pasted.strip():
                    try:
                        instance_data = json.loads(pasted)
                        st.success("JSON parsed successfully.")
                    except json.JSONDecodeError as exc:
                        st.error(f"Could not parse JSON: {exc}")

            selected_schema_label = st.selectbox(
                "Local schema",
                list(local_schema_options.keys()),
                help="Select a local JSON Schema for structural validation.",
            )
            selected_schema_path = local_schema_options.get(selected_schema_label, "")

            validate_button = st.button(
                "Validate",
                type="primary",
                use_container_width=True,
                disabled=(instance_data is None),
            )

        if validate_button and instance_data is not None:
            schema_file_path = str(REPOSITORY_ROOT / selected_schema_path) if not selected_schema_path.startswith(str(REPOSITORY_ROOT)) else selected_schema_path
            try:
                schema = load_json_schema(schema_file_path)
                report = validate_product_passport_json(instance_data, schema)
                report["schema_file"] = selected_schema_path
                report["instance_file"] = "(uploaded/pasted)"
                st.session_state["pp_validation_report"] = report
            except (FileNotFoundError, Exception) as exc:
                st.error(f"Validation error: {exc}")

        val_report = st.session_state.get("pp_validation_report")
        if val_report is not None:
            with st.container(border=True):
                render_section_header(
                    3,
                    "Validation Result",
                    "Structural schema validation result.",
                )
                status = val_report.get("validation_status", "unknown")
                error_count = len(val_report.get("errors", []))
                warning_count = len(val_report.get("warnings", []))
                s_col, e_col, w_col = st.columns(3)
                status_label = {
                    "valid": "Structural schema check: Passed",
                    "invalid": "Structural schema check: Failed — review schema errors",
                    "schema_error": "Schema could not be evaluated",
                    "not_run": "Not run",
                }.get(status, status)
                s_col.metric("Structural schema check", status_label)
                e_col.metric("Schema errors", error_count)
                w_col.metric("Validator warnings", warning_count)

                if val_report.get("errors"):
                    st.markdown("**Schema validation errors**")
                    error_rows = [{"#": i + 1, "error": e} for i, e in enumerate(val_report["errors"])]
                    st.dataframe(pd.DataFrame(error_rows), hide_index=True, use_container_width=True)

                if val_report.get("validator_mode") == "minimal_fallback":
                    st.warning(
                        "Fallback validator in use (jsonschema not available): only "
                        "required-field presence was checked. A 'Passed' result here "
                        "is weaker than full structural schema validation."
                    )

                if val_report.get("warnings"):
                    for warn in val_report["warnings"]:
                        st.info(warn)

                st.caption(f"Validator: {val_report.get('validator_version', 'unknown')}")
                st.caption(val_report.get("prototype_warning", ""))

                render_download_intro(
                    "Structural validation report JSON",
                    "Full structural validation report for offline review. Prototype/reference only — not official GS1 validation.",
                    "JSON",
                )
                st.download_button(
                    "Download structural validation report JSON",
                    data=json.dumps(val_report, indent=2, ensure_ascii=False).encode("utf-8"),
                    file_name="product_passport_validation_report.json",
                    mime="application/json",
                    use_container_width=True,
                )

    with tab_examples:
        with st.container(border=True):
            render_section_header(
                1,
                "Reference Examples",
                "Example and EPCIS example entries from the source manifest. "
                "Local committed examples can be previewed below. "
                "Placeholder entries require a separate download.",
            )
            st.info(
                "Prototype/reference examples only. Not official GS1 or DPP production data. "
                "The minimal example is committed to the repository for structural testing."
            )

        if pp_manifest_data:
            example_entries = [
                s for s in pp_manifest_data.get("sources", [])
                if s.get("source_type") in ("example", "epcis_example")
            ]
            if example_entries:
                example_rows = [
                    {
                        "source_id": e.get("source_id", ""),
                        "title": e.get("title", ""),
                        "sector": e.get("sector", ""),
                        "source_type": e.get("source_type", ""),
                        "local_path": e.get("local_path", ""),
                    }
                    for e in example_entries
                ]
                st.dataframe(
                    pd.DataFrame(example_rows),
                    hide_index=True,
                    use_container_width=True,
                )

                selected_example_id = st.selectbox(
                    "Preview example",
                    [e.get("source_id", "") for e in example_entries],
                )
                selected_example = next(
                    (e for e in example_entries if e.get("source_id") == selected_example_id),
                    None,
                )
                if selected_example:
                    local_path = selected_example.get("local_path", "")
                    example_file = REPOSITORY_ROOT / local_path if local_path else None
                    if example_file and example_file.is_file():
                        try:
                            example_data = json.loads(example_file.read_text(encoding="utf-8"))
                            with st.expander("Example JSON preview (prototype/reference only — not production data)", expanded=True):
                                st.json(example_data)
                        except (json.JSONDecodeError, OSError) as exc:
                            st.warning(f"Could not load example: {exc}")
                    else:
                        st.info(
                            f"Local file not yet available: `{local_path}`. "
                            "This is a placeholder entry. Download the file from the URL in the source manifest "
                            "and place it at the path shown."
                        )
            else:
                st.info("No example entries found in the source manifest.")
        else:
            st.info("Source manifest could not be loaded.")


def _render_build_product_passport_workflow() -> None:
    """Render the Build Product Passport Prototype workflow page."""
    st.markdown(
        """
        <div class="pp-prototype-warning">
          <strong>Prototype / Reference only — minimal-schema mode</strong>
          This builder wraps GS1 Web Vocabulary JSON-LD into a prototype Product
          Passport envelope and runs structural validation against a local
          schema (the built-in minimal schema by default). It is not official
          GS1 validation, not EU DPP regulatory compliance, and not
          production-ready.
        </div>
        """,
        unsafe_allow_html=True,
    )

    minimal_schema_path = str(REPOSITORY_ROOT / PP_BUILDER_DEFAULT_SCHEMA)
    example_path = (
        REPOSITORY_ROOT
        / "product_passport"
        / "examples"
        / "gs1_product_for_passport_builder.jsonld"
    )

    tab_input, tab_settings, tab_output, tab_report = st.tabs([
        "Input GS1 JSON-LD",
        "Builder Settings",
        "Product Passport Output",
        "Validation Report",
    ])

    with tab_input:
        with st.container(border=True):
            render_section_header(
                1,
                "Input GS1 JSON-LD",
                "Provide GS1 Web Vocabulary JSON-LD from the converter, the "
                "Manual JSON-LD Prototype Builder, or paste/upload your own.",
            )
            st.info(
                "Prototype/reference only. Minimal-schema mode. Structural "
                "validation only."
            )

        input_mode = st.radio(
            "Input mode",
            ["Upload file", "Paste JSON", "Use example"],
            horizontal=True,
        )
        gs1_data: dict | None = None
        if input_mode == "Upload file":
            uploaded = st.file_uploader(
                "GS1 JSON-LD file",
                type=["json", "jsonld"],
                help="Upload GS1 Web Vocabulary JSON-LD for wrapping.",
            )
            if uploaded is not None:
                try:
                    gs1_data = normalize_gs1_jsonld_input(
                        uploaded.getvalue().decode("utf-8")
                    )
                    st.success(f"Loaded: {uploaded.name}")
                except (ValueError, UnicodeDecodeError) as exc:
                    st.error(f"Could not parse JSON-LD: {exc}")
        elif input_mode == "Paste JSON":
            pasted = st.text_area(
                "Paste GS1 JSON-LD",
                height=200,
                placeholder='{\n  "@context": "https://ref.gs1.org/voc/data/gs1Voc.jsonld",\n  "@type": "gs1:Product",\n  "gtin": "09521234543213"\n}',
            )
            if pasted.strip():
                try:
                    gs1_data = normalize_gs1_jsonld_input(pasted)
                    st.success("JSON-LD parsed successfully.")
                except ValueError as exc:
                    st.error(f"Could not parse JSON-LD: {exc}")
        else:
            if example_path.is_file():
                try:
                    gs1_data = normalize_gs1_jsonld_input(
                        example_path.read_text(encoding="utf-8")
                    )
                    st.success(
                        "Loaded built-in example GS1 JSON-LD "
                        "(prototype/example only, not production data)."
                    )
                except (ValueError, OSError) as exc:
                    st.error(f"Could not load example: {exc}")
            else:
                st.info("Example GS1 JSON-LD not available.")

        if gs1_data is not None:
            st.session_state["pb_gs1_input"] = gs1_data

        current_gs1 = st.session_state.get("pb_gs1_input")
        if current_gs1 is not None:
            with st.container(border=True):
                render_section_header(
                    2,
                    "Parsed Summary",
                    "Fields detected in the GS1 JSON-LD input.",
                )
                summary_rows = [
                    {"field": "@type", "value": str(current_gs1.get("@type", ""))},
                    {"field": "@id", "value": extract_product_identifier(current_gs1) or ""},
                    {"field": "gtin", "value": extract_gtin(current_gs1) or ""},
                    {"field": "productName", "value": extract_product_name(current_gs1) or ""},
                    {"field": "brand", "value": extract_brand(current_gs1) or ""},
                ]
                st.dataframe(
                    pd.DataFrame(summary_rows),
                    hide_index=True,
                    use_container_width=True,
                )

    with tab_settings:
        with st.container(border=True):
            render_section_header(
                1,
                "Builder Settings",
                "Configure the prototype passport envelope. Minimal-schema mode.",
            )
            st.warning(
                "Minimal-schema mode. Structural validation only. Not official "
                "GS1 validation, not EU DPP regulatory compliance, and not "
                "production-ready."
            )
        setting_passport_id = st.text_input(
            "Passport id (optional)",
            help="Leave blank to derive a prototype id from the GTIN.",
        )
        setting_language = st.selectbox(
            "Default language",
            ["en", "nl", "de", "fr", "es"],
            index=0,
        )
        setting_include_source = st.checkbox(
            "Include source GS1 JSON-LD inside the passport envelope",
            value=True,
        )
        st.selectbox(
            "Validation schema",
            ["dpp_minimal — Minimal DPP Structural Schema (built-in)"],
            help="The built-in minimal schema is the only active validation "
            "target in v0.13.0.",
        )
        st.caption(
            "External DPP schemas listed in the source manifest are placeholders "
            "(not downloaded) and are unavailable for building until downloaded."
        )
        st.session_state["pb_settings"] = {
            "passport_id": setting_passport_id or None,
            "default_language": setting_language,
            "include_source_gs1_jsonld": setting_include_source,
        }

    with tab_output:
        with st.container(border=True):
            render_section_header(
                1,
                "Product Passport Output",
                "Build the prototype passport and preview it. Prototype/reference "
                "only.",
            )
        current_gs1 = st.session_state.get("pb_gs1_input")
        build_clicked = st.button(
            "Build Product Passport Prototype",
            type="primary",
            use_container_width=True,
            disabled=(current_gs1 is None),
        )
        if current_gs1 is None:
            st.markdown(
                """
                <div class="empty-state">
                  <span class="empty-state-mark" aria-hidden="true">PB</span>
                  <div>
                    <strong>Provide GS1 JSON-LD first</strong>
                    <span>Add input in the "Input GS1 JSON-LD" tab, then build the prototype passport here.</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if build_clicked and current_gs1 is not None:
            settings = dict(st.session_state.get("pb_settings", {}))
            settings["validation_schema"] = minimal_schema_path
            passport = build_minimal_product_passport(current_gs1, settings)
            report = validate_built_product_passport(passport, minimal_schema_path)
            st.session_state["pb_passport"] = passport
            st.session_state["pb_report"] = report

        built_passport = st.session_state.get("pb_passport")
        built_report = st.session_state.get("pb_report")
        if built_passport is not None:
            summary = build_product_passport_summary(built_passport, built_report or {})
            with st.container(border=True):
                render_section_header(2, "Summary", "Prototype passport metrics.")
                m1, m2, m3 = st.columns(3)
                m1.metric("Source GTIN", summary.get("sourceGtin") or "—")
                m2.metric(
                    "Structural schema check",
                    {
                        "valid": "Passed",
                        "invalid": "Failed",
                        "schema_error": "Could not be evaluated",
                    }.get(
                        summary.get("structuralValidationStatus"),
                        summary.get("structuralValidationStatus") or "—",
                    ),
                )
                m3.metric("Validator", summary.get("validatorMode") or "—")

            with st.container(border=True):
                render_section_header(
                    3,
                    "Prototype Product Passport JSON-LD",
                    "Prototype/reference only — not official GS1 validation.",
                )
                st.json(built_passport)
                render_download_intro(
                    "Product Passport JSON-LD",
                    "Prototype Product Passport envelope for offline review.",
                    "JSON-LD",
                )
                st.download_button(
                    "Download Product Passport JSON-LD",
                    data=product_passport_to_json_bytes(built_passport),
                    file_name="product_passport.jsonld",
                    mime="application/ld+json",
                    use_container_width=True,
                )

    with tab_report:
        with st.container(border=True):
            render_section_header(
                1,
                "Validation Report",
                "Structural schema validation of the built passport.",
            )
        report = st.session_state.get("pb_report")
        if report is None:
            st.info(
                "Build a Product Passport in the Product Passport Output tab to "
                "see the validation report."
            )
        else:
            status = report.get("validation_status", "unknown")
            status_label = {
                "valid": "Structural schema check: Passed",
                "invalid": "Structural schema check: Failed — review errors",
                "schema_error": "Schema could not be evaluated",
            }.get(status, status)
            col_status, col_errors = st.columns(2)
            col_status.metric("Structural schema check", status_label)
            col_errors.metric("Schema errors", len(report.get("errors", [])))

            if report.get("validator_mode") == "minimal_fallback":
                st.warning(
                    "Fallback validator in use (jsonschema not available): only "
                    "required-field presence was checked. A 'Passed' result here "
                    "is weaker than full structural schema validation."
                )

            if report.get("errors"):
                error_rows = [
                    {"#": idx + 1, "error": err}
                    for idx, err in enumerate(report["errors"])
                ]
                st.dataframe(
                    pd.DataFrame(error_rows),
                    hide_index=True,
                    use_container_width=True,
                )

            for warn in report.get("warnings", []):
                st.info(warn)

            st.caption(f"Validator: {report.get('validator_version', 'unknown')}")
            st.info(
                "Passing this check means only that the JSON matches the "
                "selected local structural schema. It is not an official GS1 "
                "validation or EU DPP compliance result."
            )
            render_download_intro(
                "Validation report JSON",
                "Structural validation report for offline review.",
                "JSON",
            )
            st.download_button(
                "Download validation report JSON",
                data=product_passport_report_bytes_json(report),
                file_name="product_passport_validation_report.json",
                mime="application/json",
                use_container_width=True,
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
    if st.session_state.get("selected_route") not in {
        route["key"] for route in ROUTES
    }:
        st.session_state["selected_route"] = DEFAULT_ROUTE

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
              <strong>Standards workbench</strong>
              <span>App version: {APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Compact workspace status/context — not the primary work area.
        st.markdown(
            """
            <div class="vocabulary-status">
              <strong>Workspace status</strong>
              Mode: Prototype / review<br>
              Storage: In-memory<br>
              Warnings: visible (not suppressed)
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(
                '<p class="sidebar-label">Current context</p>',
                unsafe_allow_html=True,
            )
            selected_profile = st.selectbox(
                "Mapping profile",
                list(mapping_profiles),
                on_change=clear_all_results,
                help=(
                    "Active mapping profile. It also applies inside Convert "
                    "GDSN XML. Changing it clears current conversion results."
                ),
            )
            mapping_path = mapping_profiles[selected_profile]
            st.markdown("**Active mapping file**")
            st.code(mapping_path.relative_to(REPOSITORY_ROOT).as_posix())

        with st.expander("Profile coverage & supported groups", expanded=False):
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

        st.markdown('<p class="sidebar-label">Sources</p>', unsafe_allow_html=True)
        webvoc_metadata = _load_webvoc_metadata()
        render_vocabulary_status(
            webvoc_metadata.get("detected_version"),
            webvoc_metadata.get("detected_last_modified"),
        )
        st.markdown(
            """
            <div class="vocabulary-status">
              <strong>Product Passport schemas</strong>
              Built-in minimal schema (offline).<br>
              External DPP schemas: placeholders, not downloaded.<br>
              Prototype/reference only.
            </div>
            """,
            unsafe_allow_html=True,
        )

        backlog = _load_open_standards_backlog()
        render_standards_backlog_status(
            len(backlog),
            _backlog_categories(backlog),
        )
        st.markdown(
            """
            <div class="standards-backlog-status">
              <strong>Governance</strong>
              No official GS1 validation.<br>
              No production compliance claim.
            </div>
            """,
            unsafe_allow_html=True,
        )

    modes_by_key = {mode["key"]: mode for mode in WORKFLOW_MODES}
    routes_by_key = {route["key"]: route for route in ROUTES}

    with st.container(border=True):
        render_workflow_entry_intro()

        # Stage 1 — three primary route cards (progressive disclosure).
        st.markdown(
            '<p class="workflow-group-label">Choose a route</p>',
            unsafe_allow_html=True,
        )
        route_columns = st.columns(len(ROUTES))
        for column, route in zip(route_columns, ROUTES, strict=True):
            with column:
                route_selected = st.session_state["selected_route"] == route["key"]
                render_route_card(
                    route["title"],
                    route["description"],
                    route["outcome"],
                    route["marker"],
                    route_selected,
                )
                st.button(
                    "Active" if route_selected else "Open",
                    key=f"route_{route['key']}",
                    type="primary" if route_selected else "secondary",
                    disabled=route_selected,
                    on_click=set_route,
                    args=(route["key"],),
                    use_container_width=True,
                )

        # Stage 2 — only the child workflow cards for the selected route.
        active_route = routes_by_key[st.session_state["selected_route"]]
        st.markdown(
            f'<p class="route-child-heading">{active_route["child_heading"]}</p>',
            unsafe_allow_html=True,
        )
        child_keys = active_route["children"]
        child_columns = st.columns(len(child_keys))
        for column, key in zip(child_columns, child_keys, strict=True):
            mode = modes_by_key[key]
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
    elif workflow_mode == "Generate Mapping Candidates":
        _render_mapping_candidates_workflow()
    elif workflow_mode == "Validate Product Passport Sources":
        _render_validate_product_passport_workflow()
    elif workflow_mode == "Build Product Passport Prototype":
        _render_build_product_passport_workflow()
    else:
        _render_standards_review_mode(backlog)


if __name__ == "__main__":
    main()
