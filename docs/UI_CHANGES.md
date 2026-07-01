# UI Changes

## v0.13.2 Workspace layout & theme navigation checklist

- [x] Main container max-width raised to ~82rem (≈1310px); not full-bleed;
      long text still constrained. Mobile/tablet breakpoints (900/640px) intact.
- [x] Sidebar reframed as compact workspace status/context: Workspace status
      (version, mode, storage, warnings-visible), Current context (profile +
      active file), Sources (WebVoc + Product Passport schemas), Governance.
- [x] Supported-group chips moved into a collapsed expander.
- [x] Landing page grouped under themes: Recommended path, Vocabulary & Mapping,
      JSON-LD Prototyping, Product Passport Bridge. Convert is the recommended
      start (large card + cue).
- [x] Workflow card copy shortened to one sentence + one outcome line.
- [x] Validate Product Passport Sources vs Build Product Passport Prototype are
      clearly distinguished.
- [x] Traceability rail labelled "Core conversion traceability" with a
      prototype/reference note for Product Passport workflows.
- [x] Hero copy/badges compacted (In-memory, BMS/XPath traceable, Review-only,
      Prototype Passport). Privacy/trust messaging preserved.
- [x] All seven workflows reachable; governance warnings preserved; no
      compliance claims.

**Width strategy:** a single CSS override on `[data-testid="stMainBlockContainer"]`
(`max-width: 82rem`) widens the canvas. Streamlit `st.columns` manage their own
responsive stacking, so exact 2-column control at ~800px is not reliably
achievable via CSS alone; the themed grouping caps rows at three cards as the
practical mitigation.

## Convert GDSN XML — guided four-step flow

- [x] Convert (Single XML) is presented as a guided four-step flow with a
      progress indicator: Upload → Mapping → Validate → Export (colour-coded
      teal/amber/orange/green step accents).
- [x] Wired to the real converter/validator/reporter — no mock data, no
      fabricated coverage or compliance claims.
- [x] Step 1 Upload: real uploader + "Convert product to JSON-LD" (active
      mapping profile shown inline).
- [x] Step 2 Review mapping & evidence: real mapping-trace preview.
- [x] Step 3 Generate & validate: real validation status, product identity
      (@id), and generated JSON-LD preview.
- [x] Step 4 Export & actions: the four real downloads (JSON-LD, mapping XLSX,
      validation JSON, unmapped JSON), review guidance, and Clear results.
- [x] All seven workflows remain reachable; governance warnings unchanged.
- [x] Existing behaviour, session persistence, and downloads preserved
      (result-survives-rerun, clear-results, and profile-change tests pass).

## v0.13.0 Build Product Passport Prototype workflow checklist

- [x] `Build Product Passport Prototype` workflow card is visible (marker: PB).
- [x] Overview grid is a 4+3 layout for seven workflows.
- [x] Top prototype/reference, minimal-schema-mode warning is shown.
- [x] Input GS1 JSON-LD tab: upload / paste / use-example; parsed summary.
- [x] Builder Settings tab: passport id, default language, include-source
      checkbox; built-in minimal schema active; placeholders shown unavailable.
- [x] Product Passport Output tab: build button, JSON preview, summary metrics,
      download Product Passport JSON-LD.
- [x] Validation Report tab: structural schema check status, validator mode,
      errors, download report; explicit "not official GS1 validation" caveat.
- [x] No official GS1 validation or production/EU DPP compliance claim.
- [x] No Crosswalk, SHACL execution, or VC UI.
- [x] Existing six workflows remain available.

## v0.12.1 Product Passport Bridge hardening checklist

- [x] Workflow-entry narrative names all six workflows (Convert, Explore,
      Create JSON-LD Prototype, Generate Mapping Candidates, Validate Product
      Passport Sources, Standards Review).
- [x] Schema Validator: placeholder schemas with no downloaded file are not
      offered as selectable validation targets; they are listed as unavailable.
- [x] Schema Validator: status wording changed to "Structural schema check:
      Passed / Failed / could not be evaluated" (no compliance implication).
- [x] Schema Validator: fallback validator (jsonschema unavailable) surfaces a
      visible warning.
- [x] No new workflow cards; still 6 cards in 3+3 grid.
- [x] No accept/apply button, no online fetch, no production compliance claim.

## v0.12.0 Validate Product Passport Sources workflow card checklist

- [x] `Validate Product Passport Sources` workflow card is visible (marker: PP).
- [x] Workflow selector still asks "What do you want to do?"
- [x] 6 workflow cards displayed in 3+3 grid layout.
- [x] Top-level prototype/reference warning is shown (PP Bridge warning).
- [x] Source Inventory tab: Load manifest button, counts by type/sector, source table, download JSON/CSV.
- [x] Schema Validator tab: Upload/paste JSON, schema selector, Validate button, status/errors/warnings display, download report.
- [x] Examples tab: List of example entries, preview for local files.
- [x] No accept/apply button exists.
- [x] No production compliance claim exists.
- [x] No online fetch button exists.
- [x] Existing workflows (XML, VOC, LD, SDR, MAP) remain available.

## v0.11.0 Generate Mapping Candidates workflow card checklist

- [x] `Generate Mapping Candidates` workflow card is visible (marker: MAP).
- [x] Workflow selector still asks "What do you want to do?"
- [x] 5 workflow cards displayed in 3+2 grid layout.
- [x] Top-level review-only warning is shown on entering the workflow.
- [x] WebVoc property selector appears ("All properties" plus individual IDs).
- [x] Confidence levels multiselect appears.
- [x] Review statuses multiselect appears.
- [x] "Include already mapped" checkbox appears.
- [x] "Include low confidence" checkbox appears.
- [x] Limit per property number input appears.
- [x] "Generate Candidates" button appears.
- [x] After generation: metrics (total, high/medium/low/review_required/already_mapped).
- [x] Candidate table with WebVoc property, GDSN name, BMS ID, score, confidence, review status, top reason, SDR linked.
- [x] Detail expander for selected candidate appears.
- [x] JSON download button appears.
- [x] CSV download button appears.
- [x] XLSX download button appears (if openpyxl available).
- [x] No accept/apply button exists.
- [x] No mapping YAML edit capability exists.
- [x] Existing workflows (XML, VOC, LD, SDR) remain available.

## v0.10.0 Manual JSON-LD Builder checklist

- [x] `Create JSON-LD Prototype` workflow card is visible.
- [x] Workflow selector still asks "What do you want to do?"
- [x] Root class selector appears with Product as the supported v0.10 root.
- [x] Product category selector appears.
- [x] Default language selector appears with `en`, `nl`, `de`, and `fr`.
- [x] Thematic group selector appears.
- [x] Core Product Information fields render from the builder manifest.
- [x] Entering GTIN updates the generated `@id`.
- [x] Entering `productName` updates the live JSON-LD preview.
- [x] Empty fields are omitted.
- [x] JSON-LD download appears.
- [x] Prototype/governance warning is visible.
- [x] Explorer remains read-only and points to the separate Builder workflow.
- [x] Converter, Bulk ZIP, and Standards Review workflows remain available.
- [x] Streamlit-native controls preserve keyboard/focus behaviour.

## v0.9.0 Web Vocabulary Explorer checklist

- [x] Explore GS1 Web Vocabulary mode opens as a real read-only Explorer.
- [x] WebVoc version, class count, property count, mapped properties, and
  standards-review properties appear as status metrics.
- [x] Group selector appears.
- [x] Domain selector appears.
- [x] Coverage filter appears.
- [x] Search box appears for property, label, comment, and evidence text.
- [x] Mapped-only and standards-review-only filters appear.
- [x] Property table is readable and includes coverage, evidence, and SDR
  indicators.
- [x] Property detail expander shows term metadata, BMS/XPath evidence, and
  SDR/governance notes.
- [x] Manual JSON-LD Builder panel points to the v0.10.0 Builder workflow.
- [x] Explorer remains read-only and does not expose mapping edit or YAML
  generation actions.
- [x] v0.8.0 visual language is preserved: restrained navy/blue base,
  traceability/evidence wording, XML/VOC/SDR accents, and no generic
  template-looking UI.

## v0.8.0 workflow mode quality checklist

- [x] Workflow selector is visible and asks "What do you want to do?"
- [x] Workflow cards show title, explanation, practical outcome, and active
  state.
- [x] Single XML workflow still works from the `Convert GDSN XML` mode.
- [x] Bulk ZIP workflow is visible and has clear safety copy.
- [x] Batch result dashboard is readable, with counts, validation
  issues/warnings, table preview, and export ZIP download.
- [x] Standards Review mode is readable and clearly read-only.
- [x] Explorer placeholder is visible and framed as planned functionality.
  Replaced by the read-only Explorer in v0.9.0.
- [x] Responsive layout is checked through Streamlit regression tests and a
  live HTTP startup probe.
- [x] The UI uses GS1/product-data traceability language rather than generic
  template cards or decorative AI-style visuals.
- [x] The traceability rail is the main process story; the hero side panel is
  reduced to workspace posture and does not duplicate the rail.
- [x] Workflow actions use short `Open` / `Active` labels connected to the
  workflow cards.

## Run locally

From the repository root:

```bash
python -m streamlit run app/streamlit_app.py
```

Stop any older Streamlit process first, run the command from the current
checkout, and hard-refresh the browser if it still has an older app session.

## Changed UI files

- `app/ui.py`
- `app/streamlit_app.py`
- `DESIGN.md`
- `docs/design-direction.md`
- `docs/UI_IMPLEMENTATION_PLAN.md`
- `docs/UI_CHANGES.md`

## What changed visually

- Added a premium dashboard composition pass:
  - the hero is shorter and now includes a compact workspace posture panel;
  - a traceability rail explains source XML, mapping evidence, JSON-LD output,
    and standards governance context;
  - workflow mode cards ask "What do you want to do?" before the user chooses
    conversion, vocabulary exploration, or standards review;
  - the upload control has a clearer dropzone and a purpose-built empty state;
  - profile coverage is shown as compact badges instead of a long bullet list;
  - product identity is presented as a dedicated dashboard card;
  - JSON-LD and mapping previews use labelled expandable report areas.
- Added a dedicated post-conversion review dashboard:
  - four compact summary cards confirm JSON-LD generation, validation status,
    mapped-row coverage, and unmapped-field entries;
  - validation and product identity are presented together as the first review
    checkpoint;
  - full JSON-LD remains copyable inside a calmer, collapsed preview;
  - the mapping preview states mapped versus total rows before the dataframe;
  - downloads form a labelled 2x2 export package with JSON-LD, XLSX, and JSON
    file-type badges;
  - a final "What to review next" card gives a five-step review sequence.
- Added a restrained standards-oriented hero with a product title, version
  chip, privacy context, and traceability cues.
- Introduced shared spacing, radius, color, surface, and interaction tokens.
- Added a muted page background with high-contrast white panels, blue top
  accents, stronger borders, and visible depth.
- Grouped the sidebar into a version block, bordered conversion settings, and
  an expandable profile-coverage section.
- Grouped upload, result review, mapping preview, and downloads into cards with
  prominent numbered step badges.
- Added short descriptions to product identity, JSON-LD, and mapping previews.
- Added a dedicated success, warning, or error summary card after conversion.
- Arranged downloads as four individually labelled cards in a two-column grid
  on wider screens.
- Made primary, secondary, and download actions consistently full-width.
- Strengthened primary and download button styling while retaining visible
  focus, reduced-motion support, and narrow-screen padding.
- Added a native spinner during conversion.
- Updated the visible app version from `v0.3.0-dev` to the current release
  version.

## What was intentionally not changed

- Converter, mapping, validation, CLI, and reporting logic.
- Mapping YAML files and generated JSON-LD structure.
- Session-state keys, rerun behavior, result persistence, or reset behavior.
- Mapping-profile options or their default selection.
- Download count, contents, filenames, or formats.
- Production dependencies.

## Manual review checklist

- [ ] Compact hero and right-side workspace posture panel are visible.
- [ ] Traceability rail appears below the hero.
- [ ] Workflow cards ask "What do you want to do?" and show the active mode.
- [ ] Version shows the current app version in both the hero and sidebar.
- [ ] Step 1 has a styled upload dropzone and polished empty state.
- [ ] Sidebar version, conversion settings, and supported groups are visibly
  separated and coverage appears as compact badges.
- [ ] Keyboard focus is visible on convert, download, and reset actions.
- [ ] Success or validation status appears in a distinct status card.
- [ ] Product identity is shown as a dedicated card.
- [ ] Four output summary cards appear at the top of Step 2.
- [ ] JSON-LD preview is clearly labelled, expandable, and fully copyable.
- [ ] Mapping preview shows mapped-row coverage before the dataframe.
- [ ] Four downloads appear as labelled cards in a two-column grid after
  conversion, each with a file-type badge.
- [ ] "What to review next" guidance appears below the export package.
- [ ] JSON-LD and report data match the existing generated outputs.
- [ ] Hero, workflow cards, traceability rail, and download grid stack cleanly
  at a narrow width.
- [ ] Results remain visible after reruns and download interactions.
- [ ] Changing the mapping profile clears stale results.

## Manual screenshot

No screenshot tooling is required. With the app open, capture one desktop image
after conversion that includes the compact hero, traceability rail, workflow
cards, Step 2 status, and Step 3 download grid. Capture a second image with the
browser narrowed to approximately 390 CSS pixels to confirm that the hero,
workflow cards, traceability rail, and columns stack while controls remain
usable.

## Known limitations

- Streamlit controls retain framework-defined markup and some theme behavior.
- The CSS uses stable Streamlit `data-testid` hooks for the main container,
  sidebar, and bordered containers; these should be rechecked after major
  Streamlit upgrades.
- Automated tests verify behavior, not pixel-level presentation.
- A human visual review is still required across common browser widths and
  operating-system font rendering.
