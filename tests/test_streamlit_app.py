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


def _open_workflow(app: AppTest, workflow_key: str) -> None:
    """Direct navigation (v0.30.0): open one of the five workflows."""
    _button_by_key(app, f"workflow_mode_{workflow_key}").click().run(timeout=20)


def test_ui_imports_as_package_from_non_repo_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(ROOT))
    sys.modules.pop("app.ui", None)

    ui = importlib.import_module("app.ui")

    assert ui.APP_VERSION == "v0.34.0"
    assert callable(ui.render_page_header)
    assert callable(ui.render_workflow_mode_card)


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
    assert len(app.get("download_button")) == 5  # 5th = product report HTML (v0.32.0)
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
    assert len(app.get("download_button")) == 5  # 5th = product report HTML (v0.32.0)
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
    # Codelist validation itself adds no download (5 = the standard export set).
    assert len(app.get("download_button")) == 5  # 5th = product report HTML (v0.32.0)

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


def test_readiness_scorecard_appears_after_conversion(example_xml_path):
    """v0.31.0: the DPP readiness scorecard renders in step 3 with real
    per-dimension values, an honest not-yet-assessed DPP-relevance
    dimension, and no 5th download."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)

    assert not app.exception
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "DPP readiness" in rendered

    metrics_by_label = {m.label: m.value for m in app.metric}
    assert "Structural validation" in metrics_by_label
    assert "Codelist conformance" in metrics_by_label
    # Example fixture: 2 unknown codelist values -> issues found.
    assert metrics_by_label["Codelist conformance"] == "issues found"
    # DPP relevance is never fabricated pending the Crosswalk (v0.36.0+).
    assert metrics_by_label["DPP relevance"] == "Not yet assessed"
    # Mapping coverage renders as mapped/total from the real conversion.
    assert "/" in metrics_by_label["Mapping coverage"]

    # Scope note wording is no-claims-safe and visible.
    captions = "\n".join(str(c.value) for c in app.caption).lower()
    assert "not official gs1 validation" in captions
    assert "no production compliance" in captions

    # The scorecard itself adds no download (5 = the standard export set).
    assert len(app.get("download_button")) == 5  # 5th = product report HTML (v0.32.0)


def test_product_report_download_and_journey_bridge(example_xml_path):
    """v0.32.0: (1) Convert offers a self-contained HTML product report as
    a 5th download; (2) "Continue to Product Passport" carries the
    converted JSON-LD into the passport builder, which still parses it
    through its normal input path."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    app.get("file_uploader")[0].set_value(
        ("example_product.xml", example_xml_path.read_bytes(), "application/xml")
    )
    app.run(timeout=20)
    app.button[_button_index(app, "Convert product to JSON-LD")].click().run(timeout=20)
    assert not app.exception

    report_downloads = [
        d
        for d in app.get("download_button")
        if "product report" in d.label.lower()
    ]
    assert len(report_downloads) == 1

    # v0.34.0: the GS1 Digital Link panel shows the URI form for the
    # example GTIN with the no-resolution caveat (constructed offline).
    assert any(
        code.value == "https://id.gs1.org/01/08712345678906"
        for code in app.code
    )
    assert any(
        "does not check or claim" in str(caption.value)
        for caption in app.caption
    )

    app.button[
        _button_index(app, "Continue to Product Passport")
    ].click().run(timeout=20)

    assert not app.exception
    assert app.session_state["workflow_mode"] == "Product Passport"
    assert app.session_state["journey_bridge_gtin"] == "08712345678906"

    # Both Product Passport tabs render an "Input mode" radio (the
    # validator tab has its own); select the builder's by its options.
    bridge_option = "Converted in this session (GTIN 08712345678906)"
    bridge_radio = next(r for r in app.radio if bridge_option in r.options)
    # The bridged option is offered first and pre-selected, and its payload
    # goes through the same parser as an uploaded file.
    assert bridge_radio.value == bridge_option
    assert any(
        "parsed and validated exactly" in success.value
        for success in app.success
    )
    # Converter output uses the namespaced key.
    assert app.session_state["pb_gs1_input"].get("gs1:gtin") == "08712345678906"


def test_convert_wizard_progress_indicator_present():
    """The Convert workflow shows the guided four-step progress indicator."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "convert-progress" in rendered
    for label in ("Upload", "Mapping", "Validate", "Export"):
        assert label in rendered


def test_workbench_status_dashboard_appears_on_landing_page():
    """v0.27.0: the landing page shows an at-a-glance workbench status
    panel aggregating metrics already computed by existing workflows --
    no new data, no new computation."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    assert not app.exception
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    assert "Workbench status" in rendered

    metrics_by_label = {m.label: m.value for m in app.metric}
    for expected_label in (
        "WebVoc coverage",
        "Registry accepted",
        "Open SDRs",
        "Codelists imported",
        "Builder fields authored",
        "Hard-mapping reviews (session)",
    ):
        assert expected_label in metrics_by_label

    # Cross-check against the same real local data other workflows already
    # display, so the aggregation is verified, not just "some value".
    assert metrics_by_label["Open SDRs"] == "6"
    assert metrics_by_label["Codelists imported"] == "595"
    assert metrics_by_label["Builder fields authored"] == "183"
    # Session-only metric with no candidates generated yet this run.
    assert metrics_by_label["Hard-mapping reviews (session)"] == "—"


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
        "App version: v0.34.0" in markdown.value
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
# Direct navigation (v0.30.0): five workflows, one stage
# ---------------------------------------------------------------------------


def test_direct_navigation_default_workflow_and_convert():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)

    assert "Choose a workflow" in rendered
    # All five workflow cards are visible directly on the landing page.
    for title in (
        "Convert GDSN XML",
        "Explore GS1 Web Vocabulary",
        "Create JSON-LD Prototype",
        "Mapping Governance",
        "Product Passport",
    ):
        assert title in rendered

    assert app.session_state["workflow_mode"] == "Convert GDSN XML"
    assert app.get("file_uploader")[0].label == "GDSN product XML"
    assert app.get("file_uploader")[1].label == "GDSN XML batch ZIP"
    assert any(
        "Only XML files in the ZIP are processed. Files are handled in memory"
        in info.value
        for info in app.info
    )


def test_each_workflow_opens_via_direct_navigation():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    _open_workflow(app, "prototype")
    assert app.session_state["workflow_mode"] == "Create JSON-LD Prototype"
    _open_workflow(app, "governance")
    assert app.session_state["workflow_mode"] == "Mapping Governance"
    _open_workflow(app, "product_passport")
    assert app.session_state["workflow_mode"] == "Product Passport"
    _open_workflow(app, "explore")
    assert app.session_state["workflow_mode"] == "Explore GS1 Web Vocabulary"
    _open_workflow(app, "convert")
    assert app.session_state["workflow_mode"] == "Convert GDSN XML"


def test_explore_and_standards_open_directly():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
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

    _open_workflow(app, "governance")
    assert app.session_state["workflow_mode"] == "Mapping Governance"
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
    _open_workflow(app, "governance")

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

    # Mapping Governance also renders the Candidates tab's uploaders, so
    # select the freshness uploader by label rather than position.
    freshness_uploader = next(
        u
        for u in app.get("file_uploader")
        if u.label == "Candidate gs1Voc.jsonld"
    )
    freshness_uploader.set_value(
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


def test_sdr_review_annotation_grid_renders_without_changing_status():
    """v0.29.0 slice, v0.33.0 presentation: the annotation section renders
    as a data-editor grid (one row per open SDR). AppTest cannot interact
    with st.data_editor (no accessor), so this asserts the section renders
    cleanly and applies no status transition; the annotation-building logic
    itself is covered by the pure build_sdr_review_annotation unit tests in
    tests/test_standards_backlog.py."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "governance")

    assert not app.exception
    assert any(
        "Record a review annotation" in markdown.value for markdown in app.markdown
    )
    # No annotation authored yet in a fresh session -> download hidden,
    # nudge caption shown instead.
    assert any(
        "Set a Proposed status" in caption.value for caption in app.caption
    )
    assert not [
        d for d in app.get("download_button") if "annotation" in d.label.lower()
    ]
    # Still 6 open SDRs -- the grid never applies a transition.
    assert any(
        metric.label == "Open SDRs" and metric.value == "6" for metric in app.metric
    )


def test_builder_expansion_analysis_opens_in_builder_and_is_read_only():
    """Track C (v0.19.0): read-only analysis, never claims DPP relevance,
    never touches the builder manifest, and reports real coverage numbers.
    Since v0.30.0 it lives as a tab inside Create JSON-LD Prototype."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "prototype")

    assert app.session_state["workflow_mode"] == "Create JSON-LD Prototype"
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


def test_mapping_governance_card_visible_on_landing():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)

    assert "Mapping Governance" in rendered_markdown
    assert "Review-only reports and sign-offs" in rendered_markdown


def test_mapping_candidate_warning_text_appears():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)

    _open_workflow(app, "governance")

    assert app.session_state["workflow_mode"] == "Mapping Governance"
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
    _open_workflow(app, "governance")

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


def test_hard_mapping_signoff_authoring_produces_downloadable_json():
    """v0.25.0: in-UI authoring for the hard-mapping review sign-off file.
    Setting a Decision to Approved should surface a download button; the
    downloaded JSON must match mapping_promotion.load_reviewed_hard_mappings'
    expected schema. This is authoring convenience only -- it does not
    itself change promotion eligibility in the same run."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "governance")

    property_selector = next(
        s for s in app.selectbox if s.label == "WebVoc property"
    )
    property_selector.select("gs1:gtin").run(timeout=20)
    generate_button = next(
        b for b in app.button if b.label == "Generate Candidates"
    )
    generate_button.click().run(timeout=30)

    assert not app.exception
    assert any(
        "Author hard-mapping review sign-off" in markdown.value
        for markdown in app.markdown
    )
    decision_selectors = [s for s in app.selectbox if s.label == "Decision"]
    assert len(decision_selectors) > 0

    reviewer_inputs = [t for t in app.text_input if t.label == "Reviewer"]
    decision_selectors[0].select("Approved").run(timeout=20)
    reviewer_inputs = [t for t in app.text_input if t.label == "Reviewer"]
    reviewer_inputs[0].set_value("Alice").run(timeout=20)

    assert not app.exception
    assert any(
        "1 approved, 0 rejected" in caption.value for caption in app.caption
    )
    signoff_downloads = [
        d for d in app.get("download_button") if "sign-off" in d.label.lower()
    ]
    assert len(signoff_downloads) == 1


def test_view_in_explorer_deep_link_from_candidate_detail():
    """v0.26.0: clicking 'View in Explorer' on a candidate's WebVoc property
    switches to the Explore workflow with that property pre-selected,
    instead of requiring the reviewer to manually re-search."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "governance")

    property_selector = next(
        s for s in app.selectbox if s.label == "WebVoc property"
    )
    property_selector.select("gs1:gtin").run(timeout=20)
    generate_button = next(
        b for b in app.button if b.label == "Generate Candidates"
    )
    generate_button.click().run(timeout=30)

    view_in_explorer_buttons = [
        b for b in app.button if b.label == "View in Explorer"
    ]
    assert len(view_in_explorer_buttons) == 1
    view_in_explorer_buttons[0].click().run(timeout=20)

    assert not app.exception
    assert app.session_state["workflow_mode"] == "Explore GS1 Web Vocabulary"
    assert app.session_state["webvoc_explorer_selected_property"] == "gs1:gtin"
    detail_selector = next(
        s for s in app.selectbox if s.label == "Selected property detail"
    )
    assert detail_selector.value == "gs1:gtin"
    assert "gs1:gtin" in [code.value for code in app.code]


def test_load_previously_generated_candidate_report():
    """v0.28.0: uploading a previously generated candidate report (e.g.
    from the CLI's --full-scope sweep) renders through the exact same
    metrics/table UI as a live "Generate Candidates" run, without
    re-running the expensive scoring."""
    import json as json_module

    fake_report = [
        {
            "candidate_id": "cand_a",
            "webvoc_property_id": "gs1:gtin",
            "gdsn_attribute_name": "gtin",
            "gdsn_bms_id": "1",
            "score": 0.9,
            "confidence_level": "high",
            "review_status": "already_mapped",
            "review_lane": "standard",
            "hard_mapping": False,
            "hard_mapping_reasons": [],
            "reasons": [],
            "warnings": [],
            "blocking_notes": [],
            "linked_sdr_ids": [],
        },
        {
            "candidate_id": "cand_b",
            "webvoc_property_id": "gs1:brandOwner",
            "gdsn_attribute_name": "brandOwnerGln",
            "gdsn_bms_id": "2",
            "score": 0.5,
            "confidence_level": "medium",
            "review_status": "proposed",
            "review_lane": "hard_mapping",
            "hard_mapping": True,
            "hard_mapping_reasons": ["cross-reference"],
            "reasons": [],
            "warnings": [],
            "blocking_notes": [],
            "linked_sdr_ids": [],
        },
    ]
    report_bytes = json_module.dumps(fake_report).encode("utf-8")

    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "governance")

    report_uploader = next(
        u
        for u in app.get("file_uploader")
        if "previously generated candidate report" in u.label
    )
    report_uploader.set_value(
        ("mapping_candidates.json", report_bytes, "application/json")
    ).run(timeout=20)
    load_button = next(b for b in app.button if b.label == "Load report")
    load_button.click().run(timeout=20)

    assert not app.exception
    assert any(
        "Loaded 2 candidate(s)" in success.value for success in app.success
    )
    metric_labels = {m.label: m.value for m in app.metric}
    assert metric_labels["Total candidates"] == "2"
    assert metric_labels["Standard lane"] == "1"
    assert metric_labels["Hard-mapping lane"] == "1"
    assert metric_labels["Eligible for promotion"] == "1"


def test_product_passport_workflow_shows_sources_and_structural_validation():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "product_passport")
    assert app.session_state["workflow_mode"] == "Product Passport"
    rendered_markdown = "\n".join(markdown.value for markdown in app.markdown)

    assert "structural validation" in rendered_markdown.lower()

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
    _open_workflow(app, "product_passport")
    assert app.session_state["workflow_mode"] == "Product Passport"

    schema_selects = [s for s in app.selectbox if s.label == "Local schema"]
    assert schema_selects, "Local schema selectbox not found"
    options = list(schema_selects[0].options)
    joined = " ".join(options).lower()

    assert any("dpp_minimal" in opt for opt in options), "built-in minimal missing"
    assert "dpp_general_product_schema" not in joined
    assert "dpp_battery_schema" not in joined
    assert "dpp_textile_schema" not in joined


def test_build_product_passport_warning_and_minimal_mode():
    """The passport builder tab shows prototype/minimal-schema warning, no
    official-validation or compliance claim. Since v0.30.0 it is a tab
    inside the single Product Passport workflow."""
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    _open_workflow(app, "product_passport")
    assert app.session_state["workflow_mode"] == "Product Passport"

    rendered = "\n".join(markdown.value for markdown in app.markdown)
    normalized = " ".join(rendered.split()).lower()
    assert "minimal-schema mode" in normalized
    assert "prototype" in normalized
    assert "not official gs1 validation" in normalized
    assert "not production-ready" in normalized


def test_five_workflows_and_narrative_present():
    app = AppTest.from_file("app/streamlit_app.py").run(timeout=20)
    rendered = "\n".join(markdown.value for markdown in app.markdown)
    for title in (
        "Convert GDSN XML",
        "Explore GS1 Web Vocabulary",
        "Create JSON-LD Prototype",
        "Mapping Governance",
        "Product Passport",
    ):
        assert title in rendered, f"Workflow card not present: {title}"
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
    assert "app version: v0.34.0" in rendered
    assert "no official gs1 validation" in rendered
    assert "no production compliance" in rendered
