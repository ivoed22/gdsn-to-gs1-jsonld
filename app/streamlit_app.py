import streamlit as st

st.set_page_config(
    page_title="GDSN to GS1 JSON-LD Converter",
    page_icon="🔗",
    layout="wide"
)

st.title("GDSN to GS1 JSON-LD Converter")

st.markdown(
    """
    Convert GDSN product XML into GS1 Web Vocabulary JSON-LD using configurable mappings.

    This is the first placeholder version of the web app.
    The converter engine will be added in the next development step.
    """
)

uploaded_file = st.file_uploader(
    "Upload a GDSN product XML file",
    type=["xml"]
)

if uploaded_file is not None:
    xml_content = uploaded_file.read().decode("utf-8", errors="replace")

    st.success("XML file uploaded successfully.")

    with st.expander("Preview uploaded XML"):
        st.code(xml_content[:5000], language="xml")

    st.warning("The actual GDSN to JSON-LD conversion engine is not implemented yet.")
else:
    st.info("Upload a GDSN XML file to start.")
