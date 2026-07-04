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


def _button_by_key(app: AppTest, key: str):
    for button in app.button:
        if getattr(button, "key", None) == key:
            return button
    raise AssertionError(f"button with key {key!r} not found")


def _open_route(app: AppTest, route_key: str) -> None:
    """Guided route navigation stage 1: select a primary route."""
    _button_by_key(app, f"route_{route_key}").click().run(timeout=20)


def _open_workflow(app: AppTest, workflow_key: str) -> None:
    """Guided route navigation stage 2: open a child workflow."""
    _button_by_key(app, f"workflow_mode_{workflow_key}").click().run(timeout=20)


def test_ui_imports_as_package_from_non_repo_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(ROOT))
    sys.modules.pop("app.ui", None)

    ui = importlib.import_module("app.ui")

    assert ui.APP_VERSION == "v0.24.0"
    assert callable(ui.render_page_header)
    assert callable(ui.render_route_card)


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


def test_codelist_validation_panel_appears_after_conversion(example_xml_path):
    """v0.21.0 (Track D UI wiring): the codelist validation panel is
    read-only diagnostic info and must never add a 5th download or change
    the existing conversion output."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)

    assert not app.exception
    assert any(
        "codelist validation" in expander.label.lower() for expander in app.expander
    )
    # Still exactly 4 downloads — codelist validation adds no new download.
    assert len(app.get("download_button")) == 4

    metrics_by_label = {metric.label: metric.value for metric in app.metric}
    for expected_label in ("Valid", "Unknown", "Deprecated", "Missing", "Source Unavailable"):
        assert expected_label in metrics_by_label
    # The example fixture has 5 valid codelist values and 2 unknown
    # (DPP_DOCUMENT/CERTIFICATION_DOCUMENT — documented experimental
    # sentinel values, not real GS1 ReferencedFileTypeCode values).
    assert metrics_by_label["Valid"] == "5"
    assert metrics_by_label["Unknown"] == "2"

    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "status-badge-" in rendered


def test_convert_wizard_progress_indicator_present():
    """The Convert workflow shows the guided four-step progress indicator."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "convert-progress" in rendered
    for label in ("Upload", "Mapping", "Validate", "Export"):
        assert label in rendered


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


def _archived_profile_selectbox(app: AppTest):
    for selector in app.selectbox:
        if getattr(selector, "key", None) == "archived_profile_choice":
            return selector
    raise AssertionError("archived_profile_choice selectbox not found")


def test_streamlit_mapping_registry_is_default_profile():
    """The consolidated registry is the current/default mapping artifact;
    old profiles are archived behind an expander (reference only)."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    selector = _archived_profile_selectbox(app)
    assert selector.options == [
        "None — use current registry",
        "Certifications & Documents v0.3.0 (archived)",
        "Food v0.2.0 mapping (archived)",
        "MVP v0.1.0 mapping (archived)",
    ]
    assert selector.value == "None — use current registry"

    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Active mapping profile" in rendered
    assert "Consolidated mapping registry (current)" in rendered
    assert "status-badge-current" in rendered
    assert any(
        "mapping/mapping_registry.yaml" in code.value for code in app.code
    )
    # No archived-profile warning while the registry is active.
    assert not any(
        "Archived profile" in warning.value for warning in app.warning
    )

    assert any(
        "App version: v0.24.0" in markdown.value
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


# ---------------------------------------------------------------------------
# Guided route navigation (v0.13.3)
# ---------------------------------------------------------------------------


def test_route_navigation_default_route_and_convert():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)

    assert "What do you want to do?" in rendered
    # Stage 1 — three primary route cards ("&" is HTML-escaped in card markup).
    assert "Create GS1 JSON-LD" in rendered
    assert "Vocabulary &amp; Mapping" in rendered
    assert "Product Passport Bridge" in rendered
    # Stage 2 — only the default route's children are revealed.
    assert "Choose how to create JSON-LD" in rendered
    assert "Convert GDSN XML" in rendered
    assert "Create JSON-LD Prototype" in rendered
    # Other routes' children are hidden until the route is selected.
    assert "Explore GS1 Web Vocabulary" not in rendered
    assert "Validate Product Passport Sources" not in rendered
    assert "Build Product Passport Prototype" not in rendered

    assert app.session_state["selected_route"] == "jsonld_creation"
    assert app.session_state["workflow_mode"] == "Convert GDSN XML"
    assert app.get("file_uploader")[0].label == "GDSN product XML"
    assert app.get("file_uploader")[1].label == "GDSN XML batch ZIP"
    assert any(
        "Only XML files in the ZIP are processed. Files are handled in memory"
        in info.value
        for info in app.info
    )


def test_route_headings_and_rail_visible():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Choose a route" in rendered
    for route_title in (
        "Create GS1 JSON-LD",
        "Vocabulary &amp; Mapping",
        "Product Passport Bridge",
    ):
        assert route_title in rendered
    assert "Choose how to create JSON-LD" in rendered
    assert "Core conversion traceability" in rendered


def test_route_switching_reveals_child_workflows():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    _open_route(app, "vocabulary_mapping")
    assert app.session_state["selected_route"] == "vocabulary_mapping"
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Choose a review tool" in rendered
    for title in (
        "Explore GS1 Web Vocabulary",
        "Generate Mapping Candidates",
        "Standards Review",
        "Builder Manifest Expansion Analysis",
    ):
        assert title in rendered
    assert app.session_state["workflow_mode"] == "Explore GS1 Web Vocabulary"

    _open_route(app, "product_passport_bridge")
    assert app.session_state["selected_route"] == "product_passport_bridge"
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Choose a Product Passport tool" in rendered
    for title in (
        "Validate Product Passport Sources",
        "Build Product Passport Prototype",
    ):
        assert title in rendered
    assert app.session_state["workflow_mode"] == "Validate Product Passport Sources"


def test_each_workflow_opens_via_route_then_child():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    # Create GS1 JSON-LD route (default) children.
    _open_workflow(app, "prototype")
    assert app.session_state["workflow_mode"] == "Create JSON-LD Prototype"
    _open_workflow(app, "convert")
    assert app.session_state["workflow_mode"] == "Convert GDSN XML"

    # Vocabulary & Mapping route.
    _open_route(app, "vocabulary_mapping")
    assert app.session_state["workflow_mode"] == "Explore GS1 Web Vocabulary"
    _open_workflow(app, "candidates")
    assert app.session_state["workflow_mode"] == "Generate Mapping Candidates"
    _open_workflow(app, "standards")
    assert app.session_state["workflow_mode"] == "Standards Review"
    _open_workflow(app, "builder_expansion")
    assert app.session_state["workflow_mode"] == "Builder Manifest Expansion Analysis"

    # Product Passport Bridge route.
    _open_route(app, "product_passport_bridge")
    assert app.session_state["workflow_mode"] == "Validate Product Passport Sources"
    _open_workflow(app, "product_passport_builder")
    assert app.session_state["workflow_mode"] == "Build Product Passport Prototype"


def test_explore_and_standards_open_via_route():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "vocabulary_mapping")
    _open_workflow(app, "explore")
    assert app.session_state["workflow_mode"] == "Explore GS1 Web Vocabulary"
    assert any(
        metric.label == "WebVoc version" and metric.value == "1.17"
        for metric in app.metric
    )
    assert any(metric.label == "Classes" for metric in app.metric)
    assert any(metric.label == "Properties" for metric in app.metric)
    assert any("Class reference" in expander.label for expander in app.expander)
    assert any(selector.label == "Group" for selector in app.selectbox)
    assert any(selector.label == "Coverage status" for selector in app.selectbox)
    assert app.text_input[0].label == "Search properties"

    _open_workflow(app, "standards")
    assert app.session_state["workflow_mode"] == "Standards Review"
    assert any(metric.label == "Open SDRs" and metric.value == "6" for metric in app.metric)
    assert any("docs/standards-decisions/index.md" in code.value for code in app.code)


def test_standards_review_vocabulary_freshness_check_is_offline_and_diffs_terms(
    tmp_path,
):
    """v0.24.0: Standards Review gains an offline vocabulary freshness
    check -- upload a candidate WebVoc JSON-LD and see new/removed/changed
    terms against the pinned local snapshot. Never fetches anything; the
    comparison file is provided by the reviewer."""
    import json as json_module
    from pathlib import Path

    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "vocabulary_mapping")
    _open_workflow(app, "standards")

    assert any(
        "Vocabulary freshness check" in markdown.value for markdown in app.markdown
    )
    assert any(
        "never fetches vocabulary resources itself" in markdown.value
        for markdown in app.markdown
    )

    root = Path(__file__).resolve().parents[1]
    local = json_module.loads(
        (root / "webvoc" / "current" / "gs1Voc.jsonld").read_text(
            encoding="utf-8-sig"
        )
    )
    local["@graph"].append(
        {"@id": "gs1:brandNewTestTerm", "@type": "owl:DatatypeProperty"}
    )
    candidate_bytes = json_module.dumps(local).encode("utf-8")

    app.get("file_uploader")[0].set_value(
        ("candidate.jsonld", candidate_bytes, "application/ld+json")
    )
    app.run(timeout=20)

    assert not app.exception
    metrics_by_label = {metric.label: metric.value for metric in app.metric}
    assert metrics_by_label["New terms"] == "1"
    assert metrics_by_label["Changed terms"] == "0"
    assert any(
        "1 new, 0 removed, 0 changed term(s) detected" in warning.value
        for warning in app.warning
    )


def test_builder_expansion_analysis_opens_via_route_and_is_read_only():
    """Track C (v0.19.0): read-only analysis, never claims DPP relevance,
    never touches the builder manifest, and reports real coverage numbers."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "vocabulary_mapping")
    _open_workflow(app, "builder_expansion")

    assert app.session_state["workflow_mode"] == "Builder Manifest Expansion Analysis"
    assert not app.exception

    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "never modifies the builder manifest" in rendered.lower() or any(
        "never modif" in warning.value.lower() for warning in app.warning
    )
    assert any(
        "not yet assessed" in warning.value.lower() for warning in app.warning
    )

    metrics_by_label = {metric.label: metric.value for metric in app.metric}
    assert metrics_by_label.get("Authored in manifest") == "183"
    assert metrics_by_label.get("Total WebVoc properties") == "553"
    assert metrics_by_label.get("Not yet authorable") == "371"
    assert "Ready now" in metrics_by_label


def test_streamlit_manual_builder_card_and_live_jsonld_update():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    # Create JSON-LD Prototype is a child of the default route.
    _open_workflow(app, "prototype")

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


def test_builder_coverage_overview_and_status_badges(example_xml_path):
    """v0.18.0: the coverage overview table renders and per-field status
    badges reflect filled state without changing serializer output."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "prototype")

    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Coverage overview" in rendered
    assert "status-badge-" in rendered
    # Untouched required field starts as "missing", not silently "filled".
    assert "Missing (required)" in rendered or "status-badge-blocked" in rendered

    text_inputs = {t.label: i for i, t in enumerate(app.text_input)}
    app.text_input[text_inputs["gs1:gtin value"]].set_value("09501234567890").run(
        timeout=20
    )
    rendered_after_fill = "\n".join(markdown.value for markdown in app.markdown)
    assert "status-badge-accepted" in rendered_after_fill


def test_builder_search_filters_fields_without_breaking_serializer():
    """The search box narrows which fields render but never changes the
    live JSON-LD preview logic itself."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "prototype")

    # Unfiltered: both fields render.
    field_labels_default = {t.label for t in app.text_input}
    assert "gs1:gtin value" in field_labels_default
    assert "gs1:productName value" in field_labels_default

    search_input = next(
        t for t in app.text_input if t.label == "Search fields in this group"
    )
    search_input.set_value("gtin").run(timeout=20)

    field_labels_filtered = {t.label for t in app.text_input}
    assert "gs1:gtin value" in field_labels_filtered
    assert "gs1:productName value" not in field_labels_filtered


def test_builder_evidence_expander_present_for_mapped_field():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "prototype")
    assert any("Evidence" in expander.label for expander in app.expander)


def test_builder_allergen_type_offers_full_codelist_toggle():
    """v0.23.0: gs1:allergenType's manifest options are a hand-curated
    14-value EU subset; the WebVoc snapshot defines far more individuals
    for gs1:AllergenTypeCode, so a 'show full code list' checkbox should
    appear and expand the dropdown when checked. gs1:allergenLevelOf
    ContainmentCode's curated 3 already matches WebVoc's full set, so no
    checkbox should appear for it."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "prototype")

    category_select = next(
        sb for sb in app.selectbox if sb.label == "Product category"
    )
    category_select.set_value("Food / Beverage / Tobacco").run(timeout=20)
    group_select = next(sb for sb in app.selectbox if sb.label == "Thematic group")
    group_select.set_value("Allergens").run(timeout=20)

    assert not app.exception
    toggle_checkboxes = [c for c in app.checkbox if "full code list" in c.label]
    assert len(toggle_checkboxes) == 1
    assert "curated 14" in toggle_checkboxes[0].label

    allergen_type_select = next(
        sb for sb in app.selectbox if sb.label == "gs1:hasAllergen#gs1:allergenType code"
    )
    curated_option_count = len(allergen_type_select.options)

    toggle_checkboxes[0].set_value(True).run(timeout=20)

    expanded_select = next(
        sb for sb in app.selectbox if sb.label == "gs1:hasAllergen#gs1:allergenType code"
    )
    assert len(expanded_select.options) > curated_option_count

    level_select = next(
        sb
        for sb in app.selectbox
        if sb.label == "gs1:hasAllergen#gs1:allergenLevelOfContainmentCode code"
    )
    assert len(level_select.options) == 4  # 3 curated values + "— none —"


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


def test_bulk_zip_codelist_validation_panel_appears_after_conversion(example_xml_path):
    """v0.22.0: Bulk ZIP shows the same aggregate codelist validation panel
    as Single XML (v0.21.0), summed across the batch. Diagnostic only —
    adds no new download."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("example_product.xml", example_xml_path.read_bytes())

    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[1].set_value(
        ("batch.zip", buffer.getvalue(), "application/zip")
    )
    app.run(timeout=20)
    convert_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Convert ZIP batch"
    )
    app.button[convert_button].click().run(timeout=20)

    assert not app.exception
    assert any(
        "codelist validation" in expander.label.lower() for expander in app.expander
    )
    assert len(app.get("download_button")) == 1

    metrics_by_label = {metric.label: metric.value for metric in app.metric}
    assert metrics_by_label["Valid"] == "5"
    assert metrics_by_label["Unknown"] == "2"


def test_streamlit_archived_profile_selection_warns_and_clears_results(
    example_xml_path,
):
    """Selecting an archived profile clears results, shows a visible warning,
    and switches the active mapping file (reference/comparison only)."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)
    assert "conversion_result" in app.session_state

    _archived_profile_selectbox(app).select(
        "Food v0.2.0 mapping (archived)"
    ).run(timeout=20)

    assert "conversion_result" not in app.session_state
    assert any(
        "Archived profile" in warning.value
        and "reference/comparison only" in warning.value
        for warning in app.warning
    )
    assert any(
        "mapping/mapping_v0_2.yaml" in code.value for code in app.code
    )
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "status-badge-archived" in rendered


def test_generate_mapping_candidates_card_visible_in_route():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "vocabulary_mapping")
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)

    assert "Generate Mapping Candidates" in rendered_markdown
    assert "Review-only candidate report" in rendered_markdown


def test_mapping_candidate_warning_text_appears():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    _open_route(app, "vocabulary_mapping")
    _open_workflow(app, "candidates")

    assert app.session_state["workflow_mode"] == "Generate Mapping Candidates"
    assert any(
        "review support only" in warning.value.lower()
        or "not accepted mappings" in warning.value.lower()
        for warning in app.warning
    )
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)
    assert "Generate Mapping Candidates" in rendered_markdown


def test_mapping_candidates_promotion_lanes_appear_after_generate():
    """Generating candidates shows promotion-lane metrics and lets the
    reviewer filter by lane; hard-mapping candidates start ineligible."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "vocabulary_mapping")
    _open_workflow(app, "candidates")

    property_selector = next(
        s for s in app.selectbox if s.label == "WebVoc property"
    )
    property_selector.select("gs1:gtin").run(timeout=20)

    lane_selector = next(s for s in app.selectbox if s.label == "Review lane")
    assert lane_selector.options == ["All lanes", "standard", "hard_mapping"]

    generate_button = next(
        b for b in app.button if b.label == "Generate Candidates"
    )
    generate_button.click().run(timeout=30)

    metric_labels = {m.label for m in app.metric}
    for expected in (
        "Standard lane",
        "Hard-mapping lane",
        "Eligible for promotion",
        "Hard-mapping reviews recorded",
    ):
        assert expected in metric_labels

    hard_mapping_metric = next(
        m for m in app.metric if m.label == "Hard-mapping lane"
    )
    assert int(hard_mapping_metric.value) > 0

    reviewed_metric = next(
        m for m in app.metric if m.label == "Hard-mapping reviews recorded"
    )
    assert reviewed_metric.value == "0"


def test_validate_product_passport_sources_card_visible_in_route():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "product_passport_bridge")
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)

    assert "Validate Product Passport Sources" in rendered_markdown
    assert "structural validation" in rendered_markdown.lower()


def test_product_passport_bridge_warning_text_appears():
    """PP Bridge prototype warning is visible when its route/child is active."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    _open_route(app, "product_passport_bridge")
    assert app.session_state["workflow_mode"] == "Validate Product Passport Sources"

    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)
    prototype_keywords = [
        "prototype",
        "reference only",
        "not official gs1 validation",
        "structural",
        "no production compliance",
    ]
    assert any(kw in rendered_markdown.lower() for kw in prototype_keywords), (
        f"Expected prototype/reference warning text in rendered markdown. "
        f"Got: {rendered_markdown[:500]!r}"
    )


def test_placeholder_schemas_not_offered_as_active_choices():
    """Placeholder schemas (no committed file) are not selectable validation
    targets; the built-in minimal schema is always available."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "product_passport_bridge")
    assert app.session_state["workflow_mode"] == "Validate Product Passport Sources"

    schema_selects = [s for s in app.selectbox if s.label == "Local schema"]
    assert schema_selects, "Local schema selectbox not found"
    options = list(schema_selects[0].options)
    joined = " ".join(options).lower()

    assert any("dpp_minimal" in opt for opt in options), "built-in minimal missing"
    assert "dpp_general_product_schema" not in joined
    assert "dpp_battery_schema" not in joined
    assert "dpp_textile_schema" not in joined


def test_build_product_passport_card_visible_in_route():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "product_passport_bridge")
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Build Product Passport Prototype" in rendered
    assert "PB" in rendered


def test_build_product_passport_warning_and_minimal_mode():
    """PB workflow shows prototype/minimal-schema warning, no official-validation
    or compliance claim."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_route(app, "product_passport_bridge")
    _open_workflow(app, "product_passport_builder")
    assert app.session_state["workflow_mode"] == "Build Product Passport Prototype"

    rendered = "\n".join(markdown.value for markdown in app.markdown)
    normalized = " ".join(rendered.split()).lower()
    assert "minimal-schema mode" in normalized
    assert "prototype" in normalized
    assert "not official gs1 validation" in normalized
    assert "not production-ready" in normalized


def test_three_routes_and_narrative_present():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    for route_title in (
        "Create GS1 JSON-LD",
        "Vocabulary &amp; Mapping",
        "Product Passport Bridge",
    ):
        assert route_title in rendered, f"Route not present: {route_title}"
    lowered = rendered.lower()
    assert "product passport" in lowered
    assert "mapping" in lowered


def test_convert_active_by_default_with_progress():
    """Convert is the recommended default and shows the guided Upload -> Mapping
    -> Validate -> Export progress steps."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    assert app.session_state["workflow_mode"] == "Convert GDSN XML"
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    for step in ("Upload", "Mapping", "Validate", "Export"):
        assert step in rendered, f"missing guided-convert step: {step}"


def test_sidebar_workspace_status_version_and_no_positive_compliance():
    """Sidebar is a compact workspace status/context with the current version and
    governance negations (no positive compliance claim)."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown).lower()
    assert "workspace status" in rendered
    assert "app version: v0.24.0" in rendered
    assert "no official gs1 validation" in rendered
    assert "no production compliance" in rendered
