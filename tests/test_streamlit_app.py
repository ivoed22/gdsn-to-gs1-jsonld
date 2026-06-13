from streamlit.testing.v1 import AppTest


def test_streamlit_result_survives_rerun(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run()
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run()
    app.button[0].click().run()

    assert "conversion_result" in app.session_state
    assert app.session_state["output_name_base"] == "08712345678906"
    assert len(app.get("download_button")) == 4
    assert any(
        code.value == "https://id.gs1.org/01/08712345678906"
        for code in app.code
    )

    app.run()

    assert "conversion_result" in app.session_state
    assert len(app.get("download_button")) == 4
    assert any(
        code.value == "https://id.gs1.org/01/08712345678906"
        for code in app.code
    )


def test_streamlit_clear_results_removes_persisted_result(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run()
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run()
    app.button[0].click().run()

    app.button[-1].click().run()

    assert "conversion_result" not in app.session_state
    assert len(app.get("download_button")) == 0
