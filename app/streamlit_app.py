from __future__ import annotations

import json
import sys
from pathlib import Path

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
from gdsn_to_gs1_jsonld.reporter import json_bytes, mapping_report_xlsx_bytes
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
            "Preview the planned local vocabulary browser for properties, "
            "classes, and mapping coverage."
        ),
        "outcome": "A clear placeholder for the later Explorer release.",
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


def _render_explore_placeholder() -> None:
    with st.container(border=True):
        render_section_header(
            1,
            "Explore GS1 Web Vocabulary",
            "Preview of a future vocabulary and mapping coverage explorer.",
        )
        st.info(
            "This mode will let users browse the local GS1 Web Vocabulary snapshot, "
            "inspect classes/properties, compare properties with GDSN mapping "
            "coverage, and optionally prototype manual JSON-LD. It is planned as "
            "a separate Explorer release."
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
        workflow_columns = st.columns(3)
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
        _render_explore_placeholder()
    else:
        _render_standards_review_mode(backlog)


if __name__ == "__main__":
    main()
