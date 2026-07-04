# UI Changes

## v0.25.0 In-UI hard-mapping review sign-off authoring checklist

- [x] Generate Mapping Candidates gains an "Author hard-mapping review
      sign-off" section whenever results include hard-mapping-lane
      candidates: Reviewer/Date/Decision/Notes per candidate.
- [x] "Download hard-mapping review sign-off JSON" button appears once at
      least one Decision is set; file matches
      `load_reviewed_hard_mappings`' expected schema exactly.
- [x] New `mapping_promotion.build_hard_mapping_signoff` — pure function,
      unit-tested including a round-trip through the existing loader.
- [x] Does not change `mapping_promotion.py`'s promotion logic or the
      sign-off file's schema; does not auto-apply eligibility in the same
      run; does not write to any governed file.
- [x] No governance warnings removed; no compliance claims added.

## v0.24.0 Offline vocabulary freshness check checklist

- [x] Standards Review workflow gains a "Vocabulary freshness check"
      section: upload a candidate `gs1Voc.jsonld`, see local vs uploaded
      term counts, version/modified metadata, and new/removed/changed
      term tables.
- [x] Strictly offline — `compare_webvoc_snapshot_bytes` has no `urlopen`
      call anywhere in its code path; the comparison file must be
      uploaded by the reviewer.
- [x] Diagnostic only — never writes to `webvoc/current/`, the mapping
      catalog, or any governed data.
- [x] Existing CLI `check-webvoc-updates` (optional network fetch)
      unchanged; this UI panel is a separate, always-offline capability.
- [x] No governance warnings removed; no compliance claims added.

## v0.23.0 Full WebVoc codelist option checklist

- [x] `gs1:allergenType` gains a "Show full code list (385 total) instead
      of the curated 14" checkbox; checked, the dropdown switches from the
      manifest's hand-curated EU-14 subset to every WebVoc-defined
      `AllergenTypeCode` individual. Unchecked (default) is unchanged.
- [x] Mechanism is generic (keyed off each property's own WebVoc `range`
      class) — applies automatically to any current/future `code` field
      with a smaller curated subset than WebVoc defines.
- [x] `gs1:allergenLevelOfContainmentCode` correctly gets no checkbox —
      its curated 3 values already equal WebVoc's full set.
- [x] No fabricated values: every "full list" option is a real,
      locally-committed WebVoc-defined individual.
- [x] No governance warnings removed; no compliance claims added;
      builder serializer/validator/state model unchanged (test-proven).

## v0.22.0 Bulk ZIP codelist validation checklist

- [x] Bulk ZIP workflow gains the same "Open codelist validation (Track
      D)" expander as Single XML (v0.21.0), aggregated across the batch:
      5 status metrics summed over every file, plus a table of files with
      at least one non-valid entry.
- [x] Per-file preview table gains a "codelist issues" column for
      at-a-glance triage.
- [x] `convert_batch_zip` gains a fully opt-in `codelist_registry`
      parameter; default `None` is byte-identical to every prior version.
- [x] Codelist validation never excludes a file from the batch or the
      export ZIP; batch success/failure counts unaffected.
- [x] No governance warnings removed; no compliance claims added;
      batch converter output unchanged for existing callers (test-proven).

## v0.21.0 Codelist validation UI (Track D UI wiring) checklist

- [x] Convert GDSN XML's Step 2 (Review mapping & evidence) gains an "Open
      codelist validation (Track D)" expander: 5 status metrics, a table,
      and a per-entry detail view with a status badge (reusing v0.15.0
      tokens: valid=green, unknown/deprecated=amber, missing/
      source_unavailable=grey).
- [x] Lives inside the existing Step 2 — the guided four-step structure
      (Upload/Mapping/Validate/Export) is unchanged.
- [x] Still exactly 4 downloads; codelist validation is diagnostic only,
      never added to an exported file.
- [x] If the codelist registry can't load, the panel says so and
      conversion proceeds unaffected — opt-in design preserved.
- [x] No governance warnings removed; no compliance claims added;
      converter output unchanged (test-proven).

## v0.20.0 Codelist import & enforcement (Track D)

- [x] No UI changes in this version — Track D adds an offline import
      pipeline, a validation module, and a fully opt-in converter
      parameter. Streamlit wiring for codelist validation results is a
      natural next step, not built here.

## v0.19.0 Builder manifest expansion analysis checklist

- [x] New read-only workflow "Builder Manifest Expansion Analysis" (marker
      EXP) added as a 4th child of the Vocabulary & Mapping route.
- [x] Coverage summary (authored/total/not-yet-authorable + per-phase
      counts), a readiness-phase filter (defaults to "Ready now"), a
      candidate table, and a per-candidate detail panel with a status badge
      and reasons.
- [x] No "add to manifest" control anywhere in the workflow — a top warning
      states the manifest is never modified automatically and that DPP
      relevance is not yet assessed for any candidate.
- [x] `scripts/visual_smoke.py` extended with a screen for the new
      workflow, following its own documented extension pattern.
- [x] No governance warnings removed; no compliance claims added; no DPP
      relevance claimed for any property.

## v0.18.0 Builder UX at scale checklist

- [x] Coverage overview table across every group in the selected category
      (fields, filled, missing, flagged), computed from persisted values.
- [x] Per-field status badge in the field header
      (filled=green/accepted, missing/blocked=red, review_required and
      hard_mapping_review=amber, codelist_pending=grey), reusing the
      v0.15.0 status-badge tokens; text label always present.
- [x] Search box + status multiselect scoped to the current group.
- [x] Evidence expander per field with linked catalog evidence.
- [x] Explicit "Export" section: download + clear controls with current
      group's fill/missing/flagged counts.
- [x] Fixed: controlled-vocabulary (`code`) field dropdowns now show their
      real manifest-defined options instead of only "— none —".
- [x] No governance warnings removed; no compliance claims added; builder
      serializer/validator/state model unchanged (regression-tested).

**Accessibility:** status badges pair color with text labels; search/filter
are standard labeled Streamlit inputs; evidence tables use full container
width for scannability.

## v0.17.0 Visual smoke tests checklist

- [x] No UI/UX changes — this version adds a browser-based test harness
      (`scripts/visual_smoke.py`) that asserts against the existing UI, it
      does not modify it.
- [x] Confirmed programmatically: no horizontal overflow at 1280px, active
      route/workflow buttons remain readable, every workflow shows at least
      one warning/info alert, no positive compliance claim without negation.
- [x] Screenshots captured for the landing page and all seven workflows as
      a visual record (git-ignored, uploaded as a CI artifact).

## v0.16.0 Full-scope mapping scoring & review lanes checklist

- [x] Generate Mapping Candidates gains a "Review lane" selector (all /
      standard / hard_mapping) alongside the existing property/confidence
      filters.
- [x] Optional hard-mapping review sign-off JSON upload; parsed client-side,
      never written back to any file.
- [x] Promotion-lane metrics row (standard lane, hard-mapping lane, eligible
      for promotion, hard-mapping reviews recorded) using the same metric
      style as the existing candidate metrics.
- [x] Candidate table gains Lane / Status / Eligible-for-promotion columns.
- [x] Candidate detail panel gains status/lane/promotion-eligibility badges
      (reusing the v0.15.0 status-badge tokens: accepted=green,
      review=amber, blocked=red) and a hard-mapping reasons list when
      applicable — badges always carry a text label, never color-only.
- [x] "All properties" selection shows a caption noting the true full-scope
      sweep (measured ~7 minutes) is a CLI/local operation
      (`--full-scope`), not something to run interactively for the whole
      reference set.
- [x] No governance warnings removed; no compliance claims added;
      `promotion_eligible: true` is clearly review-support only, never an
      "apply" action — the workflow still has no accept/apply button.

**Accessibility:** status/lane/eligibility badges pair color with text
labels; the review-lane and promotion-eligibility state is also visible in
the candidate table for scanning without opening the detail panel.

## v0.15.0 Mapping profile consolidation checklist

- [x] Sidebar shows a calm "Active mapping profile" panel with the profile
      name and a status badge; the consolidated registry is the default with
      a `Current` badge (blue/neutral — green stays reserved for
      pass/accepted states).
- [x] Old profiles (v0.3.0, v0.2.0, MVP) moved out of the primary flow into
      an "Archived mapping profiles" expander, labeled `(archived)` and
      muted; files kept on disk.
- [x] Selecting an archived profile shows a visible `st.warning` ("Archived
      profile — for reference/comparison only…"), switches the badge to
      `Archived` (grey), and clears current conversion results — same
      clearing behavior as the old profile selector.
- [x] New reusable status-badge component in `app/ui.py`
      (current/accepted/review/blocked/archived) built on the existing
      semantic color tokens; every badge carries a text label, never
      color-only.
- [x] Users no longer need to understand old profile history to start
      converting: the registry is active by default with no action needed.
- [x] No governance warnings removed; no compliance claims added; converter
      output unchanged (test-proven byte-identical).

**Accessibility:** badges pair color with uppercase text labels; the archived
warning is a standard Streamlit warning block (icon + text), not color-only.

## v0.13.3 Guided route navigation checklist

- [x] Landing page starts with three primary route cards: Create GS1 JSON-LD,
      Vocabulary & Mapping, Product Passport Bridge.
- [x] Route cards are visually heavier than child cards (larger title, top
      accent, monospace marker, clear active state).
- [x] Selecting a route reveals only its child workflows under a context heading
      (Choose how to create JSON-LD / Choose a review tool / Choose a Product
      Passport tool).
- [x] Default route Create GS1 JSON-LD; Convert GDSN XML is the default active
      workflow with its guided four-step flow.
- [x] Selecting a route opens its first child as active without clearing
      results; clicking a child opens the existing workflow.
- [x] All seven workflow keys unchanged and reachable.
- [x] Sidebar workspace status/context, compact hero, and core-conversion
      traceability rail preserved from v0.13.2.
- [x] No governance warnings removed; no compliance claims added.

**Responsive:** route cards use a 3-column row (Streamlit stacks on narrow
screens); child rows size to the route's child count (2 or 3) so no empty filler
cards appear. Navigation tests select route/child buttons by `key` rather than
positional index, so they stay stable across layout changes.

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
