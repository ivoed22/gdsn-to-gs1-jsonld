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
    render_status_badge,
    render_status_card,
)
from app.workflow_shared import (
    REPOSITORY_ROOT,
    clear_all_results,
    clear_batch_results,
    clear_results,
    continue_to_product_passport,
)
from gdsn_to_gs1_jsonld.batch_converter import (
    BatchConversionError,
    BatchConversionLimits,
    BatchFileResult,
    convert_batch_zip,
)
from gdsn_to_gs1_jsonld.codelist_registry import (
    CodelistRegistryError,
    load_codelist_registry,
)
from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.digital_link import (
    DIGITAL_LINK_CAVEAT,
    DigitalLinkError,
    build_digital_link_uri,
    digital_link_qr_svg,
)
from gdsn_to_gs1_jsonld.readiness import assess_readiness
from gdsn_to_gs1_jsonld.report import build_product_report_html, product_report_bytes
from gdsn_to_gs1_jsonld.reporter import json_bytes, mapping_report_xlsx_bytes
from gdsn_to_gs1_jsonld.xml_parser import XMLParseError

# Mapping profile consolidation (v0.15.0): the consolidated registry is the
# single current mapping artifact. Old profiles are archived — kept on disk
# and selectable for reference/comparison only, behind an expander with an
# explicit warning. Moved from the global sidebar into this workflow in
# v0.30.0: Convert is the only workflow that uses a mapping profile.
_CURRENT_PROFILE_LABEL = "Review-safe WebVoc profile v0.4.0 (current)"
_CURRENT_MAPPING_PATH = REPOSITORY_ROOT / "mapping" / "mapping_v0_4.yaml"
_ARCHIVED_PROFILES = {
    "Certifications & Documents v0.3.0 (archived)": (
        REPOSITORY_ROOT / "mapping" / "mapping_v0_3.yaml"
    ),
    "Food v0.2.0 mapping (archived)": (
        REPOSITORY_ROOT / "mapping" / "mapping_v0_2.yaml"
    ),
    "MVP v0.1.0 mapping (archived)": (
        REPOSITORY_ROOT / "mapping" / "mapping_mvp.yaml"
    ),
}
_NO_ARCHIVED_OPTION = "None — use current review-safe profile"


def render_mapping_profile_selector() -> Path:
    """Render the mapping-profile context and return the active mapping path.

    The archived-profile choice is read from session state before the
    expander renders (the selectbox callback updates state before the
    rerun), exactly as the sidebar version did pre-v0.30.0.
    """
    archived_choice = st.session_state.get(
        "archived_profile_choice", _NO_ARCHIVED_OPTION
    )
    archived_active = archived_choice in _ARCHIVED_PROFILES
    mapping_path = (
        _ARCHIVED_PROFILES[archived_choice]
        if archived_active
        else _CURRENT_MAPPING_PATH
    )

    with st.expander("Mapping profile", expanded=False):
        st.markdown(
            "**Active mapping profile**: "
            f"{archived_choice if archived_active else _CURRENT_PROFILE_LABEL}"
        )
        render_status_badge(
            "Archived" if archived_active else "Current",
            "archived" if archived_active else "current",
        )
        st.code(mapping_path.relative_to(REPOSITORY_ROOT).as_posix())
        st.selectbox(
            "Archived profile",
            [_NO_ARCHIVED_OPTION, *_ARCHIVED_PROFILES],
            key="archived_profile_choice",
            on_change=clear_all_results,
            help=(
                "Archived profiles are retained for reference and "
                "comparison only. Selecting one switches conversion to "
                "that profile and clears current results."
            ),
        )
    if archived_active:
        st.warning(
            "Archived profile — for reference/comparison only. The "
            "review-safe v0.4 profile is the current conversion artifact."
        )
    return mapping_path


# Status-badge tone per codelist validation status (v0.20.0 Track D).
_CODELIST_STATUS_TONES = {
    "valid": "accepted",
    "unknown": "review",
    "deprecated": "review",
    "missing": "archived",
    "source_unavailable": "archived",
}


@st.cache_data(show_spinner=False)
def _load_codelist_registry_cached() -> dict | None:
    """Load the committed codelist registry (v0.20.0), or None if missing.

    Codelist validation stays fully opt-in: if the registry can't be
    loaded, the workflow simply skips it — conversion is never affected.
    """
    try:
        return load_codelist_registry(
            REPOSITORY_ROOT
            / "reference_data"
            / "normalized"
            / "gdsn_codelists_r3_1_36.json"
        )
    except CodelistRegistryError:
        return None


def _render_codelist_validation_panel(codelist_validation: list[dict]) -> None:
    """Read-only codelist validation panel (v0.21.0, Track D UI wiring).

    Diagnostic only: never blocks conversion, never changes the four
    existing downloads. Skipped entirely if the codelist registry could
    not be loaded (codelist_validation is then an empty list).
    """
    with st.expander("Open codelist validation (Track D)", expanded=False):
        if not codelist_validation:
            st.info(
                "Codelist registry not available for this run, or no "
                "codelist-backed fields were present. See "
                "docs/codelist-registry.md."
            )
            return

        st.caption(
            "Structural check against the imported GDSN codelist registry "
            "(v0.20.0). Diagnostic only — a non-valid status never blocks "
            "conversion or changes the downloadable output."
        )
        counts: dict[str, int] = {}
        for entry in codelist_validation:
            counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        metric_columns = st.columns(len(_CODELIST_STATUS_TONES))
        for column, status in zip(metric_columns, _CODELIST_STATUS_TONES, strict=True):
            column.metric(status.replace("_", " ").title(), counts.get(status, 0))

        table_rows = [
            {
                "Canonical field": entry["canonical_field"],
                "Codelist": entry["code_list"],
                "Value": entry["value"],
                "Status": entry["status"],
            }
            for entry in codelist_validation
        ]
        st.dataframe(pd.DataFrame(table_rows), hide_index=True, width="stretch")

        selected_idx = st.selectbox(
            "Select entry for detail",
            range(len(codelist_validation)),
            format_func=lambda i: (
                f"{codelist_validation[i]['canonical_field']} "
                f"({codelist_validation[i]['status']})"
            ),
            key="codelist_validation_detail_select",
        )
        selected = codelist_validation[selected_idx]
        render_status_badge(
            selected["status"].replace("_", " ").title(),
            _CODELIST_STATUS_TONES.get(selected["status"], "archived"),
        )
        st.caption(selected["detail"])


# Status-badge tone per readiness level / dimension status (v0.31.0).
_READINESS_LEVEL_TONES = {
    "structurally_ready": "accepted",
    "attention_points": "review",
    "review_required": "blocked",
}
_READINESS_LEVEL_LABELS = {
    "structurally_ready": "Structurally ready",
    "attention_points": "Attention points",
    "review_required": "Review required",
}


def _render_readiness_scorecard(result) -> None:
    """DPP readiness scorecard (v0.31.0): traceability & structural signals.

    Pure presentation over :func:`readiness.assess_readiness` — every
    number was already computed by this conversion; nothing is re-scored
    or invented, and DPP relevance stays not-yet-assessed until the
    Crosswalk (v0.36.0+) exists.
    """
    assessment = assess_readiness(
        validation_report=result.validation_report,
        mapping_report_rows=result.mapping_report_rows,
        unmapped_fields=result.unmapped_fields,
        codelist_validation=result.codelist_validation,
    )
    dimensions = assessment["dimensions"]

    render_preview_heading(
        "DPP readiness",
        "Traceability & structural signals from this conversion.",
        "Scorecard",
    )
    level = assessment["readiness_level"]
    render_status_badge(
        _READINESS_LEVEL_LABELS.get(level, level),
        _READINESS_LEVEL_TONES.get(level, "archived"),
    )

    structural = dimensions["structural_validation"]
    coverage = dimensions["mapping_coverage"]
    codelist = dimensions["codelist_conformance"]
    relevance = dimensions["dpp_relevance"]

    columns = st.columns(4)
    columns[0].metric(
        "Structural validation",
        structural["status"].replace("_", " "),
        help=structural["detail"],
    )
    columns[1].metric(
        "Mapping coverage",
        f"{coverage['mapped_count']}/{coverage['profile_row_count']}",
        help=coverage["detail"],
    )
    columns[2].metric(
        "Codelist conformance",
        codelist["status"].replace("_", " "),
        help=codelist["detail"],
    )
    columns[3].metric(
        "DPP relevance",
        "Not yet assessed",
        help=relevance["detail"],
    )
    st.caption(assessment["scope_note"])


def _render_digital_link_panel(gtin: str | None) -> None:
    """GS1 Digital Link URI form + locally rendered QR (v0.34.0).

    Constructed offline from the GTIN only. The caveat wording comes from
    digital_link.DIGITAL_LINK_CAVEAT: nothing here checks or claims that
    the link is registered, resolvable, or live.
    """
    try:
        uri = build_digital_link_uri(gtin or "")
        qr_svg = digital_link_qr_svg(uri)
    except DigitalLinkError:
        return

    render_preview_heading(
        "GS1 Digital Link",
        "The Digital Link URI form for this GTIN, with a locally "
        "rendered QR code.",
        "URI + QR",
    )
    uri_column, qr_column = st.columns([1.6, 1])
    with uri_column:
        st.code(uri)
        st.caption(DIGITAL_LINK_CAVEAT)
    with qr_column:
        # Locally generated, trusted SVG (qrcode SvgPathImage output).
        st.markdown(
            f'<div style="max-width: 10rem;">{qr_svg}</div>',
            unsafe_allow_html=True,
        )


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
            width="stretch",
        ):
            clear_results()
            try:
                with st.spinner("Converting and validating product data..."):
                    conversion = convert_xml_to_jsonld(
                        uploaded_file.getvalue(),
                        mapping_path,
                        write_files=False,
                        codelist_registry=_load_codelist_registry_cached(),
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
                st.session_state["product_report_bytes"] = product_report_bytes(
                    build_product_report_html(
                        jsonld_data=conversion.jsonld_data,
                        validation_report=conversion.validation_report,
                        mapping_report_rows=conversion.mapping_report_rows,
                        unmapped_fields=conversion.unmapped_fields,
                        codelist_validation=conversion.codelist_validation,
                    )
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
                    width="stretch",
                )

            _render_codelist_validation_panel(result.codelist_validation)

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

            _render_readiness_scorecard(result)

            _render_digital_link_panel(result.canonical_product.gtin)

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
                "5 files",
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
                        width="stretch",
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
                        width="stretch",
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
                        width="stretch",
                    )
            with download_bottom_right:
                with st.container(border=True):
                    render_download_intro(
                        "Unmapped source values JSON",
                        "Lossless source evidence for every populated XML value "
                        "not emitted by the active profile. No properties are inferred.",
                        "JSON",
                    )
                    st.download_button(
                        "Download unmapped source values JSON",
                        data=st.session_state["unmapped_fields_bytes"],
                        file_name=f"unmapped_values_{output_name_base}.json",
                        mime="application/json",
                        width="stretch",
                    )

            with st.container(border=True):
                render_download_intro(
                    "Product report HTML",
                    "Self-contained, printable report: identity, readiness "
                    "scorecard, mapping evidence, and the JSON-LD. Opens "
                    "fully offline.",
                    "HTML",
                )
                st.download_button(
                    "Download product report (HTML)",
                    data=st.session_state["product_report_bytes"],
                    file_name=f"product_report_{output_name_base}.html",
                    mime="text/html",
                    width="stretch",
                )

            render_review_guidance()
            journey_column, clear_column = st.columns(2)
            with journey_column:
                st.button(
                    "Continue to Product Passport",
                    type="primary",
                    on_click=continue_to_product_passport,
                    width="stretch",
                    help=(
                        "Carry this product's generated JSON-LD into the "
                        "Product Passport builder. The builder still parses "
                        "and validates it exactly like an uploaded file."
                    ),
                )
            with clear_column:
                st.button(
                    "Clear results",
                    on_click=clear_results,
                    width="stretch",
                )


def _render_batch_codelist_validation_panel(
    codelist_validation_counts: dict[str, int],
    files: list[BatchFileResult],
) -> None:
    """Aggregate, read-only codelist validation panel for the Bulk ZIP batch (v0.22.0).

    Extends v0.21.0's Single XML panel to batches: sums per-file
    diagnostic counts rather than listing every field entry (a batch can
    span many files). Diagnostic only — never blocks a batch or changes
    which files succeed or fail.
    """
    with st.expander("Open codelist validation (Track D)", expanded=False):
        if not any(codelist_validation_counts.values()):
            st.info(
                "Codelist registry not available for this run, or no "
                "codelist-backed fields were present. See "
                "docs/codelist-registry.md."
            )
            return

        st.caption(
            "Structural check against the imported GDSN codelist registry "
            "(v0.20.0), aggregated across the batch. Diagnostic only — a "
            "non-valid status never blocks conversion or excludes a file "
            "from the export ZIP."
        )
        metric_columns = st.columns(len(_CODELIST_STATUS_TONES))
        for column, status in zip(metric_columns, _CODELIST_STATUS_TONES, strict=True):
            column.metric(
                status.replace("_", " ").title(),
                codelist_validation_counts.get(status, 0),
            )

        issue_rows = [
            {
                "filename": result.original_filename,
                **{
                    status.replace("_", " ").title(): result.codelist_status_counts.get(
                        status, 0
                    )
                    for status in _CODELIST_STATUS_TONES
                    if status != "valid"
                },
            }
            for result in files
            if sum(
                count
                for status, count in result.codelist_status_counts.items()
                if status != "valid"
            )
            > 0
        ]
        if issue_rows:
            st.caption("Files with at least one non-valid codelist entry:")
            st.dataframe(pd.DataFrame(issue_rows), hide_index=True, width="stretch")
        else:
            st.caption("No file had a non-valid codelist entry.")


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
            width="stretch",
        ):
            clear_batch_results()
            try:
                with st.spinner("Converting XML files from ZIP..."):
                    report = convert_batch_zip(
                        uploaded_zip.getvalue(),
                        mapping_path,
                        limits=BatchConversionLimits(),
                        codelist_registry=_load_codelist_registry_cached(),
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
                width="stretch",
                hide_index=True,
            )

            _render_batch_codelist_validation_panel(
                report.codelist_validation_counts, report.files
            )

            st.download_button(
                "Download batch export ZIP",
                data=st.session_state["batch_export_zip_bytes"],
                file_name="gdsn_batch_export.zip",
                mime="application/zip",
                width="stretch",
            )
