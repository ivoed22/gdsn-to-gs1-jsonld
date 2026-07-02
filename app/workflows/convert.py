"""Convert GDSN XML workflow (single file and bulk ZIP)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from app.ui import (
    render_convert_progress,
    render_download_intro,
    render_empty_upload_state,
    render_identity_card,
    render_preview_heading,
    render_result_summary,
    render_review_guidance,
    render_section_header,
    render_status_card,
)
from app.workflow_shared import clear_batch_results, clear_results
from gdsn_to_gs1_jsonld.batch_converter import (
    BatchConversionError,
    BatchConversionLimits,
    convert_batch_zip,
)
from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.reporter import json_bytes, mapping_report_xlsx_bytes
from gdsn_to_gs1_jsonld.xml_parser import XMLParseError


def render_single_xml_workflow(mapping_path: Path) -> None:
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


def render_bulk_zip_workflow(mapping_path: Path) -> None:
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
