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
from ui import apply_page_styles, render_page_header, render_section_header

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
st.info(
    "Privacy: uploaded XML files are processed in memory and are not "
    "intentionally stored permanently."
)

mapping_profiles = {
    "Certifications & Documents v0.3.0": (
        REPOSITORY_ROOT / "mapping" / "mapping_v0_3.yaml"
    ),
    "Food v0.2.0 mapping": REPOSITORY_ROOT / "mapping" / "mapping_v0_2.yaml",
    "MVP v0.1.0 mapping": REPOSITORY_ROOT / "mapping" / "mapping_mvp.yaml",
}

with st.sidebar:
    st.caption("CONVERSION SETTINGS")
    st.header("Mapping profile")
    selected_profile = st.selectbox(
        "Select a versioned profile",
        list(mapping_profiles),
        on_change=clear_results,
        help="Changing the profile clears the current conversion result.",
    )
    mapping_path = mapping_profiles[selected_profile]
    st.caption("App version: v0.3.0-dev")
    st.markdown("**Active mapping file**")
    st.code(mapping_path.relative_to(REPOSITORY_ROOT).as_posix())
    st.divider()
    st.caption("PROFILE COVERAGE")
    st.markdown(
        """
**Supported field groups**

- Basic product identity
- Descriptions
- Brand/category
- Net content
- Images/links
- Ingredients
- Allergens
- Nutrients
- Certifications
- DPP/document links
"""
    )

with st.container(border=True):
    render_section_header(
        "Step 1",
        "Upload product data",
        "Choose one XML product message. The source remains in memory and is "
        "not written to the repository.",
    )
    uploaded_file = st.file_uploader(
        "GDSN product XML",
        type=["xml"],
        help="Accepted format: one XML file.",
    )

    if uploaded_file is None:
        st.info("Upload one XML file to enable conversion.")
    elif st.button(
        "Convert to JSON-LD",
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
            "Step 2",
            "Review conversion result",
            "Check validation first, then inspect the product identity and "
            "generated structured data.",
        )

        validation = result.validation_report
        if validation["valid"] and not validation["warnings"]:
            st.success("Conversion completed and validation passed.")
        elif validation["valid"]:
            st.warning(
                "Conversion completed with "
                f"{len(validation['warnings'])} warning(s)."
            )
        else:
            st.error(
                "Conversion completed with "
                f"{len(validation['errors'])} validation error(s)."
            )

        product_id = result.jsonld_data.get("@id")
        if product_id:
            st.subheader("Product identity")
            st.caption("GS1 Digital Link-style product @id")
            st.code(product_id)

        st.subheader("Generated JSON-LD")
        st.caption("GS1 Web Vocabulary-aligned structured product data")
        formatted_jsonld = json.dumps(
            result.jsonld_data,
            indent=2,
            ensure_ascii=False,
        )
        st.code(formatted_jsonld, language="json")

    with st.container(border=True):
        render_section_header(
            "Step 3",
            "Inspect traceability and export",
            "Review the applied mappings and download the generated data and "
            "diagnostic reports.",
        )
        st.subheader("Mapping report preview")
        st.caption("Source fields, canonical fields, and generated properties")
        st.dataframe(
            pd.DataFrame(result.mapping_report_rows),
            use_container_width=True,
        )

        output_name_base = st.session_state["output_name_base"]
        st.subheader("Downloads")
        download_left, download_right = st.columns(2)
        with download_left:
            st.download_button(
                "Download JSON-LD",
                data=st.session_state["jsonld_bytes"],
                file_name=f"product_{output_name_base}.jsonld",
                mime="application/ld+json",
                use_container_width=True,
            )
            st.download_button(
                "Download validation report JSON",
                data=st.session_state["validation_report_bytes"],
                file_name=f"validation_report_{output_name_base}.json",
                mime="application/json",
                use_container_width=True,
            )
        with download_right:
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
            st.download_button(
                "Download unmapped fields report JSON",
                data=st.session_state["unmapped_fields_bytes"],
                file_name=f"unmapped_fields_{output_name_base}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.button(
            "Clear results",
            on_click=clear_results,
            use_container_width=True,
        )
