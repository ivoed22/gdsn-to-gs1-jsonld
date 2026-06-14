from streamlit.testing.v1 import AppTest


def test_streamlit_result_survives_rerun(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[0].click().run(timeout=20)

    assert "conversion_result" in app.session_state
    assert app.session_state["output_name_base"] == "08712345678906"
    assert len(app.get("download_button")) == 4
    assert any(
        "https://id.gs1.org/01/08712345678906" in markdown.value
        for markdown in app.markdown
    )

    app.run(timeout=20)

    assert "conversion_result" in app.session_state
    assert len(app.get("download_button")) == 4
    assert any(
        "https://id.gs1.org/01/08712345678906" in markdown.value
        for markdown in app.markdown
    )


def test_streamlit_clear_results_removes_persisted_result(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[0].click().run(timeout=20)

    app.button[-1].click().run(timeout=20)

    assert "conversion_result" not in app.session_state
    assert len(app.get("download_button")) == 0


def test_streamlit_mapping_selector_defaults_to_v0_3():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    selector = app.selectbox[0]
    assert selector.options == [
        "Certifications & Documents v0.3.0",
        "Food v0.2.0 mapping",
        "MVP v0.1.0 mapping",
    ]
    assert selector.value == "Certifications & Documents v0.3.0"
    assert any(
        "App version: v0.5.0" in markdown.value
        for markdown in app.markdown
    )
    assert any("mapping/mapping_v0_3.yaml" in code.value for code in app.code)


def test_streamlit_profile_change_clears_results(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[0].click().run(timeout=20)
    assert "conversion_result" in app.session_state

    app.selectbox[0].select("Food v0.2.0 mapping").run(timeout=20)

    assert "conversion_result" not in app.session_state
