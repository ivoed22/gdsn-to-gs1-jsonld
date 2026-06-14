import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
APP_DIRECTORY = Path(__file__).resolve().parent
SRC_DIRECTORY = REPOSITORY_ROOT / "src"
if str(APP_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(APP_DIRECTORY))
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.reporter import json_bytes, mapping_report_xlsx_bytes
from gdsn_to_gs1_jsonld.xml_parser import XMLParseError
from ui import (
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
    render_vocabulary_status,
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


def clear_results() -> None:
    for key in RESULT_STATE_KEYS:
        st.session_state.pop(key, None)


st.set_page_config(
    page_title="GDSN to GS1 JSON-LD Converter",
    page_icon="G",
    layout="wide",
)
apply_page_styles()
render_page_header()
render_workflow_overview()

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
            on_change=clear_results,
            help="Changing the profile clears the current conversion result.",
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

    webvoc_metadata_path = REPOSITORY_ROOT / "webvoc" / "current" / "metadata.json"
    webvoc_metadata = {}
    if webvoc_metadata_path.is_file():
        try:
            webvoc_metadata = json.loads(
                webvoc_metadata_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            webvoc_metadata = {}
    render_vocabulary_status(
        webvoc_metadata.get("detected_version"),
        webvoc_metadata.get("detected_last_modified"),
    )

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
