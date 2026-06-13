import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_DIRECTORY = REPOSITORY_ROOT / "src"
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld
from gdsn_to_gs1_jsonld.reporter import json_bytes, mapping_report_xlsx_bytes
from gdsn_to_gs1_jsonld.xml_parser import XMLParseError

st.set_page_config(
    page_title="GDSN to GS1 JSON-LD Converter",
    page_icon="G",
    layout="wide",
)
st.title("GDSN to GS1 JSON-LD Converter")
st.write(
    "Convert a GDSN-like product XML file into GS1 Web Vocabulary JSON-LD "
    "using a configurable mapping profile."
)
st.info(
    "Privacy: uploaded XML files are processed in memory and are not "
    "intentionally stored permanently."
)

uploaded_file = st.file_uploader("Upload a GDSN product XML file", type=["xml"])
st.selectbox("Mapping profile", ["MVP mapping"])

if uploaded_file is None:
    st.info("Upload one XML file to begin.")
elif st.button("Convert to JSON-LD", type="primary"):
    mapping_path = REPOSITORY_ROOT / "mapping" / "mapping_mvp.yaml"
    try:
        result = convert_xml_to_jsonld(
            uploaded_file.getvalue(),
            mapping_path,
            write_files=False,
        )
    except (XMLParseError, FileNotFoundError, ValueError) as exc:
        st.error(f"Conversion failed: {exc}")
    else:
        validation = result.validation_report
        if validation["valid"] and not validation["warnings"]:
            st.success("Conversion completed and validation passed.")
        elif validation["valid"]:
            st.warning(
                f"Conversion completed with {len(validation['warnings'])} warning(s)."
            )
        else:
            st.error(
                f"Conversion completed with {len(validation['errors'])} validation error(s)."
            )

        product_id = result.jsonld_data.get("@id")
        if product_id:
            st.subheader("Product @id")
            st.code(product_id)

        st.subheader("Generated JSON-LD")
        formatted_jsonld = json.dumps(
            result.jsonld_data,
            indent=2,
            ensure_ascii=False,
        )
        st.code(formatted_jsonld, language="json")

        st.subheader("Mapping report preview")
        st.dataframe(
            pd.DataFrame(result.mapping_report_rows),
            use_container_width=True,
        )

        gtin = result.canonical_product.gtin or "unknown"
        st.subheader("Downloads")
        st.download_button(
            "Download JSON-LD",
            data=json_bytes(result.jsonld_data),
            file_name=f"product_{gtin}.jsonld",
            mime="application/ld+json",
        )
        st.download_button(
            "Download mapping report XLSX",
            data=mapping_report_xlsx_bytes(result.mapping_report_rows),
            file_name=f"mapping_report_{gtin}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "Download validation report JSON",
            data=json_bytes(validation),
            file_name=f"validation_report_{gtin}.json",
            mime="application/json",
        )
        st.download_button(
            "Download unmapped fields report JSON",
            data=json_bytes(result.unmapped_fields),
            file_name=f"unmapped_fields_{gtin}.json",
            mime="application/json",
        )
