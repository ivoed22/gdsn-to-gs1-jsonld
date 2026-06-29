import importlib
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _button_index(app: AppTest, label: str, occurrence: int = 0) -> int:
    matches = [
        index for index, button in enumerate(app.button) if button.label == label
    ]
    return matches[occurrence]


def test_ui_imports_as_package_from_non_repo_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(ROOT))
    sys.modules.pop("app.ui", None)

    ui = importlib.import_module("app.ui")

    assert ui.APP_VERSION == "v0.10.0"
    assert callable(ui.render_page_header)


def test_streamlit_app_imports_package_ui_from_non_repo_cwd(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(ROOT))
    sys.modules.pop("ui", None)
    sys.modules.pop("app.streamlit_app", None)

    streamlit_app = importlib.import_module("app.streamlit_app")

    assert streamlit_app.REPOSITORY_ROOT == ROOT
    assert streamlit_app.SRC_DIRECTORY == ROOT / "src"
    assert callable(streamlit_app.main)
    assert "ui" not in sys.modules


def test_streamlit_result_survives_rerun(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)

    assert "conversion_result" in app.session_state
    assert app.session_state["output_name_base"] == "08712345678906"
    assert len(app.get("download_button")) == 4
    assert any(
        "https://id.gs1.org/01/08712345678906" in markdown.value
        for markdown in app.markdown
    )
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)
    assert "JSON-LD generated" in rendered_markdown
    assert "Mapping report" in rendered_markdown
    assert "Unmapped fields report" in rendered_markdown
    assert "What to review next" in rendered_markdown

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
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)

    app.button[_button_index(app, "Clear results")].click().run(timeout=20)

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
        "App version: v0.10.0" in markdown.value
        for markdown in app.markdown
    )
    assert any(
        "Vocabulary status" in markdown.value
        for markdown in app.markdown
    )
    assert any(
        "Standards review backlog" in markdown.value
        and "Open topics: 6" in markdown.value
        and "not runtime converter failures" in markdown.value
        for markdown in app.markdown
    )
    assert any("mapping/mapping_v0_3.yaml" in code.value for code in app.code)


def test_streamlit_workflow_modes_and_bulk_tab_are_visible():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)

    assert "What do you want to do?" in rendered_markdown
    assert "Convert GDSN XML" in rendered_markdown
    assert "Explore GS1 Web Vocabulary" in rendered_markdown
    assert "Create JSON-LD Prototype" in rendered_markdown
    assert "Standards Review" in rendered_markdown
    assert "JSON-LD plus mapping, validation" in rendered_markdown
    assert "Manual JSON-LD prototype with visible governance" in rendered_markdown
    assert app.session_state["workflow_mode"] == "Convert GDSN XML"
    assert app.button[_button_index(app, "Active")].disabled
    assert [button.label for button in app.button[:4]] == [
        "Active",
        "Open",
        "Open",
        "Open",
    ]
    assert app.get("file_uploader")[0].label == "GDSN product XML"
    assert app.get("file_uploader")[1].label == "GDSN XML batch ZIP"
    assert any(
        "Only XML files in the ZIP are processed. Files are handled in memory"
        in info.value
        for info in app.info
    )

    app.button[_button_index(app, "Open")].click().run(timeout=20)

    assert app.session_state["workflow_mode"] == "Explore GS1 Web Vocabulary"
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)
    assert "Browse the local GS1 Web Vocabulary snapshot" in rendered_markdown
    assert any(metric.label == "WebVoc version" and metric.value == "1.17" for metric in app.metric)
    assert any(metric.label == "Classes" for metric in app.metric)
    assert any(metric.label == "Properties" for metric in app.metric)
    assert any("Class reference" in expander.label for expander in app.expander)
    assert any(selector.label == "Group" for selector in app.selectbox)
    assert any(selector.label == "Coverage status" for selector in app.selectbox)
    assert app.text_input[0].label == "Search properties"
    assert any(
        "Manual JSON-LD Builder" in markdown.value
        for markdown in app.markdown
    )

    app.button[_button_index(app, "Open", occurrence=2)].click().run(timeout=20)

    assert app.session_state["workflow_mode"] == "Standards Review"
    assert any(metric.label == "Open SDRs" and metric.value == "6" for metric in app.metric)
    assert any("docs/standards-decisions/index.md" in code.value for code in app.code)


def test_streamlit_manual_builder_card_and_live_jsonld_update():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    app.button[_button_index(app, "Open", occurrence=1)].click().run(timeout=20)

    assert app.session_state["workflow_mode"] == "Create JSON-LD Prototype"
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)
    assert "Create JSON-LD Prototype" in rendered_markdown
    assert any(
        "Prototype output only" in warning.value or "Manual JSON-LD prototype" in warning.value
        for warning in app.warning
    )
    assert any(selector.label == "Root class" for selector in app.selectbox)
    assert any(selector.label == "Product category" for selector in app.selectbox)
    assert any(selector.label == "Default language" for selector in app.selectbox)
    assert any(selector.label == "Thematic group" for selector in app.selectbox)
    assert "Core Product Information" in rendered_markdown
    assert any(
        download.label == "Download prototype JSON-LD"
        for download in app.get("download_button")
    )

    text_inputs = {text_input.label: index for index, text_input in enumerate(app.text_input)}
    app.text_input[text_inputs["gs1:gtin value"]].set_value("09501234567890")
    app.text_input[text_inputs["gs1:productName value"]].set_value(
        "Example apple juice"
    )
    app.run(timeout=20)

    generated_json = "\n".join(code.value for code in app.code)
    assert '"@id": "https://id.gs1.org/01/09501234567890"' in generated_json
    assert '"gtin": "09501234567890"' in generated_json
    assert '"productName": [' in generated_json
    assert '"@language": "en"' in generated_json
    assert '"@value": "Example apple juice"' in generated_json

    group_selectbox = next(
        index for index, selector in enumerate(app.selectbox)
        if selector.label == "Thematic group"
    )
    app.selectbox[group_selectbox].select("Physical Dimensions").run(timeout=20)
    text_inputs = {text_input.label: index for index, text_input in enumerate(app.text_input)}
    app.text_input[text_inputs["gs1:netContent quantity value"]].set_value("1")
    app.text_input[text_inputs["gs1:netContent unitCode"]].set_value("LTR")
    app.run(timeout=20)

    generated_json = "\n".join(code.value for code in app.code)
    assert '"@id": "https://id.gs1.org/01/09501234567890"' in generated_json
    assert '"productName": [' in generated_json
    assert '"netContent": {' in generated_json
    assert '"unitCode": "LTR"' in generated_json

    app.button[_button_index(app, "Clear builder")].click().run(timeout=20)

    generated_json = "\n".join(code.value for code in app.code)
    assert '"@id": "https://id.gs1.org/01/09501234567890"' not in generated_json
    assert '"productName": [' not in generated_json
    assert '"netContent": {' not in generated_json


def test_streamlit_bulk_zip_conversion_produces_batch_result(sample_dir):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "minimal_product.xml",
            (sample_dir / "minimal_product.xml").read_bytes(),
        )
        archive.writestr("notes.txt", "ignored")

    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[1].set_value(
        ("sample_batch.zip", buffer.getvalue(), "application/zip")
    )
    app.run(timeout=20)
    convert_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Convert ZIP batch"
    )
    app.button[convert_button].click().run(timeout=20)

    assert "batch_conversion_report" in app.session_state
    report = app.session_state["batch_conversion_report"]
    assert report.xml_files_found == 1
    assert report.success_count == 1
    assert any(
        download.label == "Download batch export ZIP"
        for download in app.get("download_button")
    )


def test_streamlit_profile_change_clears_results(example_xml_path):
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)
    assert "conversion_result" in app.session_state

    app.selectbox[0].select("Food v0.2.0 mapping").run(timeout=20)

    assert "conversion_result" not in app.session_state
