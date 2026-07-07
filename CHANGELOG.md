# Changelog

Releases follow a tag-per-meaningful-change cadence: each notable change is cut
as its own CI-gated tag + GitHub Release rather than bundled into periodic
drops. Work in progress accumulates under `## Unreleased` below and is renamed
to its version heading when released. See `docs/roadmap.md` → "Release process".

## Unreleased

_Nothing yet._

## v0.34.0 — GS1 Digital Link Preview + QR

Fifth version of the end-product build path: the story now ends with
"and this is the URI form this product resolves under in the Digital
Link world" — honestly framed.

- New pure module `src/gdsn_to_gs1_jsonld/digital_link.py`:
  `build_digital_link_uri(gtin)` returns the GS1 Digital Link URI form
  (`https://id.gs1.org/01/{gtin}` — the exact form the converter
  already emits as `@id`), and `digital_link_qr_svg(uri)` renders it as
  a QR code SVG locally via the `qrcode` package's SVG path factory (no
  raster imaging dependency, no network, deterministic).
- **Honesty constraint built into the wording** (shared
  `DIGITAL_LINK_CAVEAT` constant, test-enforced): constructing the URI
  is offline string formatting; nothing checks or claims that the link
  is registered, resolvable, or live.
- **Convert step 3 gains a "GS1 Digital Link" panel** (after the
  readiness scorecard): the URI in a code block, the QR beside it, the
  caveat underneath. Skipped cleanly when the GTIN is unusable — never
  a placeholder QR.
- **The HTML product report embeds the same section** (URI + inline
  SVG + caveat); the report stays fully self-contained and
  deterministic.
- New dependency `qrcode` (pure Python) added to `pyproject.toml`
  dependencies and `requirements.txt` (which also lost its accidental
  duplicate entries).

## v0.33.0 — UI Overhaul Within Streamlit

Fourth version of the end-product build path: the interaction layer
catches up with the consolidated structure. Five changes, guided by the
ui-ux-pro-max design guidance (dark tokens as desaturated tonal variants,
progressive disclosure, one primary action per screen, tabular data
presentation) applied within the existing DESIGN.md token system:

- **Progressive disclosure in Mapping Governance:** the five candidate
  filter controls (confidence, review status, two include-checkboxes,
  limit per property) now sit in a collapsed "Filters" expander, so the
  page leads with the property/lane choice and its one primary action.
  All defaults unchanged.
- **Grid-style SDR annotation editing:** the six stacked four-column
  forms in Standards Review became one `st.data_editor` grid (read-only
  SDR/Title columns, editable Reviewer/Decision date/Proposed status/
  Notes, fixed status vocabulary via SelectboxColumn), feeding the same
  `build_sdr_review_annotation` helper and download. The hard-mapping
  sign-off form was deliberately left as-is this version (its AppTest
  drives real widget interactions; `st.data_editor` has no AppTest
  accessor).
- **Table presentation:** Explore's property table and the candidate
  results table gain column config — pinned key column, `%.3f` score
  formatting, checkbox rendering for promotion eligibility, compact
  status columns.
- **Dark mode (custom CSS layer):** a `prefers-color-scheme: dark`
  token set — desaturated, lightened tonal variants of the light
  tokens, not inverted colors — plus targeted overrides for the
  hardcoded light surfaces (sidebar panels, status cards, badges,
  warning boxes). Borders stay visible and text contrast holds in both
  themes; verified with a dark-emulated browser screenshot. Streamlit's
  own widgets continue to follow the user's Streamlit theme setting.
- **Deprecation sweep:** all 48 `use_container_width=True` occurrences
  replaced with `width="stretch"` (upstream removal deadline had
  passed); the per-run deprecation warnings are gone.

Visual smoke baselines regenerated (light theme). No behavior changes:
converter, serializer, validators, and all download/report outputs are
untouched.

## v0.32.0 — Product Journey Bridge + Report Center

Third version of the end-product build path: the workflows start telling
one story ("from GDSN message to Digital Product Passport"), and every
conversion produces a shareable artifact.

- **Product Journey bridge.** Convert's Export step gains "Continue to
  Product Passport": one click carries the converted product's generated
  JSON-LD into the Product Passport builder (session state) and switches
  workflows. The builder offers it as a pre-selected "Converted in this
  session (GTIN …)" input mode next to the existing upload/paste/example
  paths — and runs the bridged payload through the exact same
  `normalize_gs1_jsonld_input` parsing as an uploaded file. Transport
  convenience, never a validation bypass.
- **Report Center.** New pure module `src/gdsn_to_gs1_jsonld/report.py`
  (`build_product_report_html`): ONE self-contained, printable HTML
  report per converted product — identity, the v0.31.0 readiness
  assessment rendered verbatim (including the not-yet-assessed
  DPP-relevance dimension), mapping evidence summary, codelist counts,
  and the generated JSON-LD. Inline CSS only (DESIGN.md color tokens),
  no scripts, no external resources — opens identically fully offline.
  Deterministic: same conversion in, same bytes out. Governance
  negations render verbatim in the footer.
- **Convert now offers 5 downloads** (was 4): the product report HTML
  joins JSON-LD, mapping XLSX, validation JSON, and unmapped-fields
  JSON. The three AppTests that pinned the 4-download invariant now pin
  5.
- Visual smoke: the Mapping Governance drive now picks the property via
  keyboard (type + Enter) instead of clicking inside the BaseWeb virtual
  dropdown, which kept timing out on CI runners (non-blocking failures
  in the v0.30.0/v0.31.0 runs).

No warnings suppressed; the outward-facing report repeats — not
removes — the no-claims governance text.

## v0.31.0 — DPP Readiness Scorecard

Second version of the end-product build path: one honest, deterministic
readiness panel per converted product — the artifact a stakeholder demo
ends on.

- New pure module `src/gdsn_to_gs1_jsonld/readiness.py`
  (`assess_readiness`): summarizes *traceability & structural readiness*
  from signals the conversion already computed — structural validation
  (errors/warnings), mapping coverage (profile rows found + unmapped
  source elements), and codelist conformance (v0.20.0 registry counts).
  Nothing is re-validated, re-scored, or invented.
- **Honesty rules built in:** the DPP-relevance dimension always reports
  `not_yet_assessed_pending_crosswalk` (the Crosswalk, v0.36.0+, is not
  built — same pattern as `builder_expansion_analysis`); there is
  deliberately **no single numeric score** (any weighting between
  dimensions would be invented); the codelist dimension reports
  `not_evaluated` when no registry was used, never a fake clean result.
- Overall level from fixed, transparent rules: `review_required` on
  structural errors; `attention_points` on warnings, partial coverage,
  or codelist issues; `structurally_ready` only when every evaluated
  dimension is clean. The not-yet-assessed dimension never affects it.
- **Convert (Single XML) step 3 renders the scorecard**: level badge,
  four dimension metrics with detail tooltips, and a no-claims-safe
  scope note ("not official GS1 validation, no production compliance
  claim, no EU DPP conformity assessment"). Still exactly 4 downloads.
- Visual smoke: the Mapping Governance candidate-generation drive now
  retries once with a fresh open-type-click attempt (the v0.30.0 CI run
  showed the BaseWeb dropdown can miss the first typed filter on slow
  runners; the blocking test job was green).

## v0.30.0 — Consolidation: Nine Workflows Become Five

First version of the approved end-product build path (see
`docs/roadmap.md` → "End-product build path"): the app moves from a
toolbox of nine separate workflows toward one product with a spine.
Behavior-preserving — the converter, serializer, and validators are
untouched; only navigation, grouping, and dead UI changed.

- **Nine workflows consolidated into five:**
  - *Convert GDSN XML* (unchanged: Single XML / Bulk ZIP tabs).
  - *Explore GS1 Web Vocabulary* (unchanged).
  - *Create JSON-LD Prototype* — Builder Manifest Expansion Analysis is
    now a tab inside it (it is analysis *about* the builder manifest).
  - *Mapping Governance* (new) — Generate Mapping Candidates + Standards
    Review (SDR annotations, vocabulary freshness) merged into one
    review lifecycle.
  - *Product Passport* — the Sources/Validation workflow and the
    prototype Passport Builder merged into one workflow with tabs.
- **Direct navigation replaces the two-stage route→child cards** (they
  existed to manage nine destinations; with five they only cost clicks
  and screen height). One "Choose a workflow" row with five cards.
- **Landing page reduced** to hero → workbench status → navigation: the
  traceability strip and "workflow entry" intro sections were removed.
- **Mapping-profile selection moved from the sidebar into Convert**
  (the only workflow that uses a mapping profile), behind a low-key
  "Mapping profile" expander with the same archived-profile warning.
- **Dead UI removed:** the Builder's no-op "Product is for sale"
  checkbox (form helper that emitted nothing) and the duplicate
  governance status block in the sidebar.
- `set_route`/`ROUTES` removed from `app/workflow_shared.py`;
  `navigate_to_webvoc_property` (v0.26.0 deep link) no longer needs to
  set a route. Dead UI component helpers removed from `app/ui.py`.
- Visual smoke walks the five workflows directly; the per-screen alert
  check now retries briefly (Explore's first render builds its dataset
  and could race the assertion).

No warnings suppressed; no governance/no-claims text removed (the
sidebar keeps exactly one governance block; every workflow keeps its
scope warnings — test-enforced).

## v0.29.0 — First Slice of the Standards Review Workflow

Last of eight versions in this batch (v0.22.0–v0.29.0). Adds the smallest
useful slice of the "Standards-review workflow (future)" roadmap item —
deliberately not the full state machine it describes.

- New `standards_backlog.build_sdr_review_annotation(annotations)`: builds
  a review-annotation artifact from `{sdr_id, reviewer, decision_date,
  proposed_status, notes}` entries. `proposed_status` reuses the module's
  existing fixed `VALID_DECISION_STATUSES` vocabulary
  (`proposed`/`accepted`/`rejected`/`deferred`) — no new vocabulary
  invented.
- **Standards Review gains a "Record a review annotation" section**: one
  Reviewer/Decision-date/Proposed-status/Notes row per open SDR, and a
  "Download review annotations JSON" button once at least one status is
  set. This records a *proposal*, not an applied decision — it never
  changes an SDR's actual status and never writes to
  `docs/standards-decisions/standards_review_backlog.json` (governed
  data), consistent with how v0.25.0's hard-mapping sign-off never
  auto-applied either.
- Explicitly out of scope for this slice (left for the full workflow
  described in `docs/roadmap.md`): moving records through
  Proposed/Accepted/Rejected/Deferred, creating versioned mapping changes
  for accepted decisions, and any enforcement of the proposed status.
- `docs/roadmap.md`'s Crosswalk section renumbered from `v0.22.0+` to
  `v0.30.0+`, since this is the last version before that track resumes
  (still blocked on the user's own CIRPASS/sector-vocabulary sourcing).

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims.

## v0.28.0 — Load a Previously Generated Candidate Report

Corrects course from the originally planned scope after investigation:
the premise "the CLI's `--full-scope` sweep is too slow to run live in
Streamlit, so build a separate viewer for its output" doesn't hold —
`--full-scope` calls the exact same `generate_all_candidates` function
the UI's existing "All properties" option already calls; there is no
separate full-scope code path to view differently. The genuinely useful
and honest version of this feature: let a reviewer load a report they
already generated (via the CLI or a previous UI session) instead of
re-running an expensive multi-minute scan.

- New `app.workflows.candidates.parse_uploaded_candidate_report(raw_bytes)`
  — a pure function validating an uploaded JSON file matches the same
  shape `candidate_report_bytes_json` produces (a flat array of candidate
  dicts, each needing at least `candidate_id` and `webvoc_property_id`).
- **Generate Mapping Candidates gains a "Load a previously generated
  candidate report" uploader and "Load report" button.** Loading a report
  runs it through the exact same `build_promotion_artifact` annotation
  step as a live "Generate Candidates" run (recomputing eligibility using
  whatever hard-mapping sign-off file is currently uploaded), then
  populates the exact same session-state keys — so the existing metrics,
  table, detail expander, sign-off authoring, and downloads all work
  identically on a loaded report with no duplicated rendering code.
- New shared `_store_candidate_results` helper factors out the
  annotate-and-persist step previously duplicated only in the live-
  generation path.
- Accepts reports from either source: this workflow's own downloaded
  `mapping_candidates.json`, or the CLI's (with or without
  `--full-scope`) — both are the same JSON shape.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims — nothing here re-scores or invents candidate data; it only
re-renders and re-annotates what was already computed.

## v0.27.0 — Workbench Status Dashboard

First of three "bigger scope" versions in this batch. Every module already
computes read-only health metrics, but each only ever surfaced inside its
own workflow. This adds a consolidated "at a glance" view.

- New `app/workflows/dashboard.py` and `render_workbench_status_dashboard`,
  shown on the landing page right after the page header. Six metrics, each
  read via the same loader/function an existing workflow already uses —
  no new data source, no new computation:
  - **WebVoc coverage** — `webvoc_explorer.build_explorer_dataset`'s
    summary (same numbers Explore shows).
  - **Registry accepted** — `mapping_registry.registry_summary`'s
    `catalog_by_status["accepted"]`.
  - **Open SDRs** — the same standards backlog count already loaded for
    the sidebar (passed in, not reloaded).
  - **Codelists imported** — the committed, tiny Track D summary JSON
    (`gdsn_codelists_r3_1_36_summary.json`), not the full 4.5MB registry.
  - **Builder fields authored** — `builder_expansion_analysis.
    authored_property_ids` against the builder manifest (the same count
    Track C's analysis uses).
  - **Hard-mapping reviews (session)** — opportunistic: reads
    `st.session_state["promotion_summary"]` if the reviewer has already
    generated candidates this session, otherwise shows "—". Distinctly
    labeled from Generate Mapping Candidates' own "Hard-mapping reviews
    recorded" metric to avoid confusion, since this panel renders earlier
    in the script and can show one-rerun-stale session data.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims.

## v0.26.0 — Cross-Workflow Deep Links

The last of the five "quick win" versions in this batch. Reduces
tab-hopping between review workflows.

- New `workflow_shared.navigate_to_webvoc_property(property_id)`: an
  `st.button(on_click=...)` callback that switches the active route/
  workflow to Explore GS1 Web Vocabulary, resets Explore's filters to
  "show everything," and pre-selects the given property in its detail
  view. Pure session-state wiring — no new data, no new computation.
- **Generate Mapping Candidates' candidate detail expander gains a "View
  in Explorer" button** next to the WebVoc property code block. Clicking
  it jumps straight to that property's Explorer detail view instead of
  requiring a manual re-search.
- Explore's filter/search/detail-selection widgets gained explicit
  `key=` parameters so they can be pre-filled externally. A defensive
  guard resets the detail selectbox to the first match whenever its
  stored value is no longer among the current filtered options (e.g.
  after a manual search change) — preserving pre-v0.26.0 behavior for
  everyone not using the deep link.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims.

## v0.25.0 — In-UI Hard-Mapping Review Sign-Off Authoring

Removes the last hand-edit-JSON-externally step from the Mapping
Candidates workflow: authoring the hard-mapping review sign-off file
directly in the UI.

- New `mapping_promotion.build_hard_mapping_signoff(reviews)`: builds a
  sign-off JSON from authored `{candidate_id, reviewer, date, decision,
  notes}` entries. Only `"approved"` entries land in
  `reviewed_candidate_ids` — the one key `load_reviewed_hard_mappings`
  actually reads — so the file stays byte-compatible with hand-edited
  files and the existing loader/promotion pipeline is untouched.
  `reviews` is additive audit metadata the loader ignores.
- **Generate Mapping Candidates gains an "Author hard-mapping review
  sign-off" section**, shown whenever the current results include
  hard-mapping-lane candidates: a reviewer/date/decision/notes row per
  candidate, and a "Download hard-mapping review sign-off JSON" button
  once at least one decision is set. Convenience only — it does not
  change eligibility in the same run; upload the downloaded file through
  the existing sign-off uploader and regenerate to see updated
  eligibility.
- No changes to `mapping_promotion.py`'s promotion logic, the sign-off
  file's schema, or any governed file. The UI never auto-applies a
  sign-off; the reviewer still explicitly downloads and would separately
  commit/apply it.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims.

## v0.24.0 — Offline Vocabulary Freshness Check

Surfaces the previously CLI-only `check-webvoc-updates` capability in the
Streamlit UI, but as a strictly offline comparison — the existing CLI
command can optionally fetch GS1's live vocabulary URLs, which is fine as
an explicit, human-invoked CLI operation, but not acceptable to wire into
the app under the project's no-online-fetching rule.

- New `webvoc_monitor.compare_webvoc_snapshot_bytes(snapshot_dir,
  comparison_jsonld_bytes)`: a pure, offline diff between the pinned local
  WebVoc snapshot and a second, already-in-memory JSON-LD file. Contains
  no `urlopen` call anywhere in its code path — reuses the existing
  term-extraction/diff helpers, never reaches the network.
- **Standards Review workflow gains a "Vocabulary freshness check"
  section.** A reviewer uploads a candidate `gs1Voc.jsonld` (e.g. a newer
  official export they downloaded themselves) and sees local vs. uploaded
  term counts, version/modified metadata, and new/removed/changed term
  tables. Diagnostic only — never updates the committed snapshot, mapping
  catalog, or any governed data; that stays a separate, explicit step.
- The existing CLI `check-webvoc-updates` (with its optional network
  fetch) is unchanged and remains the way to check against GS1's live
  URLs; this UI panel is a separate, always-offline capability.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No online fetching is added anywhere in the app.

## v0.23.0 — Full WebVoc Codelist Option in Manual Builder

Corrects course from the originally planned scope after investigation: the
6 canonical fields tracked by Track D's `CODELIST_DEPENDENCIES` turned out
to already have real options where they're authorable in the builder, or
aren't authorable as `code`-type fields at all yet (see "What we found"
below). The genuinely valuable, verified gap was different — implemented
instead.

- **`gs1:allergenType`'s manifest options were a hand-curated 14-value EU
  subset of the 385 individuals the local Web Vocabulary snapshot actually
  defines for `gs1:AllergenTypeCode`.** The Manual JSON-LD Builder now
  offers a "Show full code list (385 total) instead of the curated 14"
  checkbox next to this field; checking it swaps the dropdown to the full,
  real WebVoc-defined set. Unchecked (default), behavior is unchanged.
- New `webvoc_explorer.group_individuals_by_class(data)`: groups every
  WebVoc-defined named individual (e.g. `gs1:AllergenTypeCode-AM`) by its
  class, generically, from the already-committed local snapshot. No new
  data source, no fabricated values — only individuals the vocabulary
  itself defines.
- `builder_status.compute_field_status` now also accepts an optional
  `metadata["full_codelist_options"]` fallback: a field is `codelist_pending`
  only if both the curated `options` and this fallback are empty. No field
  is affected today (every current `code` field already has curated
  options), but this keeps the status correct if a future manifest field
  ships with `options: []`.
- The mechanism is generic (keyed off each property's own WebVoc `range`
  class), so it applies automatically to any current or future builder
  `code` field — not just this one.

**What we found (why the plan changed):** all 6 `CODELIST_DEPENDENCIES`
canonical fields were checked against the builder manifest.
`gs1:allergenLevelOfContainmentCode` already has all 3 real
`LevelOfContainmentCode` values curated (no gap). `net_content_unit` is a
`quantity`-type sub-field, not a `code`-type field. `nutrient_type_code`/
`preparation_state_code` live under `gs1:nutrientDetail`, which is not yet
authorable in the builder (`supported_in_v0_10: false`). No authorable
`code` field maps to `ReferencedFileTypeCode`. Every *other* existing
`code`-type field in the manifest already had manifest-curated options.
`gs1:allergenType` was the one concrete, verified gap.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims — every added option is a real WebVoc-defined individual, not an
invented value.

## v0.22.0 — Bulk ZIP Codelist Validation

Extends v0.21.0's codelist validation panel to the Bulk ZIP workflow.
Read-only diagnostic; no converter behavior change and no new download.

- **`convert_batch_zip` gains a fully opt-in `codelist_registry` parameter**,
  mirroring `convert_xml_to_jsonld`. Leaving it `None` (the default) is
  byte-identical to every prior version. `BatchFileResult` gains a
  `codelist_status_counts` field; the batch summary gains an aggregate
  `codelist_validation_counts` dict.
- **Bulk ZIP workflow shows an aggregate "Open codelist validation (Track
  D)" expander** after conversion: five status metrics summed across the
  whole batch, plus a table of any files that had at least one non-valid
  codelist entry, so a user can see which files need attention without
  scanning every field of every file.
- Batch success/failure counts and the export ZIP contents are unaffected;
  codelist validation never blocks a file or excludes it from the export.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.21.0 — Codelist Validation UI (Track D UI Wiring)

Read-only diagnostic panel; no converter behavior change and no new
download.

- **Convert GDSN XML now shows codelist validation.** A new "Open codelist
  validation (Track D)" expander inside the existing Step 2 (Review mapping
  & evidence) shows per-field status (valid/unknown/deprecated/missing/
  source_unavailable) against the v0.20.0 codelist registry, with counts,
  a table, and a per-entry detail view with a status badge.
  `render_single_xml_workflow` now passes a cached, loaded codelist
  registry into `convert_xml_to_jsonld` — still fully consistent with the
  opt-in design: if the registry can't load, the panel says so and nothing
  else changes.
- Still exactly 4 downloads; no new file is added. Codelist validation
  results are diagnostic only, never blocking conversion or changing
  `jsonld_data`.
- On the example fixture: 5 valid, 2 unknown (the already-documented
  `DPP_DOCUMENT`/`CERTIFICATION_DOCUMENT` sentinel values).

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.20.0 — Codelist Import & Enforcement (Track D)

Unblocked this session: the user provided the official public GDSN and
Shared Common Code Lists workbook for release 3.1.36 (595 codelists,
14,564 values, 509 deprecated values) — previously the reference data had
507 codelist *names* but zero value enumerations.

- **New source, committed with provenance.**
  `reference_data/raw_public/GDSN_and_Shared_Code_Lists_r3p1p36_i6_8May2026.xlsx`,
  inventoried in `reference_data/source_manifest.json` with checksum and
  license/rights note, following the same pattern as the existing GDSN
  BMS/XPath workbook. `source_url` is a project-internal URN rather than a
  guessed public link, since the exact GS1 download URL was not
  independently confirmed.
- **New importer** `src/gdsn_to_gs1_jsonld/codelist_importer.py` and CLI
  command `import-codelists` produce a deterministic, versioned registry
  (`reference_data/normalized/gdsn_codelists_r3_1_36.json`, committed):
  codelist values, labels, definitions, status, and deprecated values with
  sunset release.
- **New validation module** `src/gdsn_to_gs1_jsonld/codelist_registry.py`:
  `validate_code_value` classifies a value as `valid` / `unknown` /
  `deprecated` / `missing` / `source_unavailable`. `CODELIST_DEPENDENCIES`
  is a curated, independently verified table (not derived from the mapping
  registry catalog's `code_list` column, which predates several field
  renames and contains at least one clearly incorrect entry).
- **Converter integration is fully opt-in.** `convert_xml_to_jsonld` gains
  an optional `codelist_registry` parameter, default `None`. Not passing it
  is byte-identical to every prior version. Passing a loaded registry only
  adds a new `ConversionResult.codelist_validation` list — `jsonld_data`
  and every other field stay identical either way. Codelist validation
  never blocks conversion by itself; warning vs. blocking is entirely a
  caller decision built on top of this data.
- On the committed example fixture, two `referenced_file_type` values come
  back `unknown` (`DPP_DOCUMENT`, `CERTIFICATION_DOCUMENT`) — a genuine,
  expected finding: they are project-defined sentinel values for the
  already-documented experimental `referencedDocument` mapping, not real
  GS1 codes.
- Not done in this version: Streamlit UI wiring (natural next step, not
  built here), and enforcement for fields outside the six verified
  dependencies.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.19.0 — Builder Manifest Expansion Analysis (Track C)

Read-only analysis; the builder manifest, mapping registry, mapping
catalog, and Web Vocabulary snapshots are all unchanged.

- **New workflow: Builder Manifest Expansion Analysis** (marker EXP), added
  under the Vocabulary & Mapping route. Shows which of the 371 WebVoc
  properties not yet authorable in the Manual JSON-LD Builder manifest
  (183 of 553 authored) are mature enough to add next, and why.
- **New module** `src/gdsn_to_gs1_jsonld/builder_expansion_analysis.py`
  classifies each not-yet-authorable property into a fixed readiness
  vocabulary — `ready_now` / `needs_codelist_curation` /
  `needs_hard_mapping_review` / `not_ready_no_evidence` — using the
  consolidated mapping registry's governance catalog (v0.15.0) and reusing
  Track B's exact `detect_hard_mapping` rules (v0.16.0) against linked GDSN
  evidence. On current data: 5 ready_now, 366 not_ready_no_evidence — a
  small ready count that honestly reflects how small the governed mapping
  registry still is.
- **DPP relevance is never assessed.** Every candidate reports
  `dpp_relevance: "not_yet_assessed_pending_crosswalk"` — that judgment
  belongs to the GS1-first DPP Crosswalk (now sequenced as v0.20.0+, moved
  back one slot to make room for this track), not fabricated here.
- **New CLI command** `analyze-builder-expansion` writes
  `builder_manifest_expansion_analysis.json`.
- No "add to manifest" action exists anywhere in the new workflow —
  approving an addition remains a separate, deliberate decision.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.18.0 — Builder UX at Scale

The manual builder's state model, serializer, and validator are unchanged;
this version adds navigation/status aids and fixes a real defect.

- **Coverage overview.** A table across every group in the selected product
  category (fields, filled, missing-required, flagged-for-review), computed
  from the same persisted values as the live preview.
- **Per-field status chips.** New `src/gdsn_to_gs1_jsonld/builder_status.py`
  (pure, unit-tested) derives one of `filled` / `missing` / `review_required`
  / `hard_mapping_review` / `codelist_pending` / `blocked` per field, shown
  as a status badge in the field header. `external_source_required` and
  `extension_candidate` are reserved vocabulary values, never triggered
  today — they need data (a promoted hard mapping; a Crosswalk gap) that
  doesn't exist yet, and no fabricated status is emitted in their place.
- **Hard-mapping review reuses Track B's detection.** The same deterministic
  `detect_hard_mapping` rules from the v0.16.0 Mapping Candidate Generator
  are applied to a field's linked GDSN evidence, flagging fields backed by a
  cross-reference (organization/party, country, cross-item product
  reference) for extra review.
- **Search, status filter, evidence expander, clearer export area** added to
  the Create JSON-LD Prototype workflow.
- **Bug fix: controlled-vocabulary (`code`) fields now show their real
  options.** The manifest's per-field `options` were parsed but never
  reached the render layer, so every code-type dropdown silently showed
  only "— none —" — e.g. `gs1:packagingMarkedLabelAccreditation`'s 30+ real
  values were unreachable. Fixed and regression-tested.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.17.0 — Visual Smoke Tests

No app behavior changes. This is read-only browsing plus assertions.

- **Browser-based visual smoke.** `scripts/visual_smoke.py` boots the app
  headless (Playwright + Chromium) and walks the landing page plus all seven
  workflows via the guided-route navigation, asserting: no horizontal
  overflow at a 1280px viewport, the active route/workflow button is
  readable, no positive compliance claim appears without negation (same
  check as `tests/test_no_claims.py`, on rendered page text), at least one
  warning/info alert visible per workflow, and the version + all three
  routes are visible on the landing page. Each screen is captured as a
  full-page screenshot.
- **New `visual` optional dependency group** (`pip install -e ".[visual]"`)
  adds `playwright` without touching the default `dev` install.
- **New CI job `visual-smoke`**, `continue-on-error: true` while the harness
  stabilizes; uploads screenshots as a build artifact rather than failing
  the run. Deliberately separate from the blocking `test` job.
- Screenshots are git-ignored (`tests/visual/baselines/`) — this version
  captures and asserts on live layout, not pixel-diff regression against a
  committed baseline; see `docs/visual-smoke.md`.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.16.0 — Full-Scope Mapping Scoring & Review Lanes

Review-only, as always: no mapping YAML, mapping registry, or mapping
catalog is written by this release. Converter behavior, batch behavior, and
single-file output are unchanged.

- **Every candidate now carries a review lane.** `hard_mapping` (bool) +
  `hard_mapping_reasons` are computed deterministically from the GDSN
  reference data (`class_associated_to`/`named_association` cross-class
  references to `Country`/`PartyIdentification`/`PartyInRole`/
  `EntityIdentification`/`TradeItemIdentification`/`CatalogueItemReference`,
  plus GLN/cross-item-GTIN attribute-name patterns). Embedded value objects
  fully contained in the product message are not flagged — nesting alone
  is not "hard." `review_lane` is `"standard"` or `"hard_mapping"`.
- **Both lanes reach the same terminal status.** New
  `src/gdsn_to_gs1_jsonld/mapping_promotion.py` computes `status` (fixed
  registry vocabulary) and `promotion_eligible`: standard-lane candidates
  are eligible once their own review_status carries no blocker; hard-mapping
  candidates are **never** eligible from scoring alone — they additionally
  require a human-curated hard-mapping review sign-off file
  (`--reviewed-hard-mappings`) before becoming eligible for the same
  `accepted` status as any other candidate. There is no
  `hard_mapping_candidate` status and no permanent block.
- **Promotion artifact.** Every `generate-mapping-candidates` run now also
  writes a reviewable `promotion/` report (summary + standard-lane +
  hard-mapping-lane + eligible-for-promotion, JSON and CSV). Nothing writes
  mapping YAML or the registry automatically.
- **`--full-scope` CLI flag.** Scores all 553 WebVoc properties against the
  full ~6,067-row GDSN attribute reference in one run (measured ~7 minutes
  on the committed reference data). Documented as local/offline use;
  intentionally not part of the CI-blocking smoke, which stays scoped to a
  single property for speed.
- **UI**: the Generate Mapping Candidates workflow gained a review-lane
  filter, an optional hard-mapping review sign-off upload, promotion-lane
  metrics, and per-candidate status/lane/eligibility badges + hard-mapping
  reasons in the detail panel. The candidate generator's cached inputs now
  read the consolidated mapping registry (`mapping/mapping_registry.yaml`)
  instead of the archived `mapping_v0_3.yaml`.
- Docs: `docs/mapping-candidate-generator.md` documents the detection rules,
  lane/promotion fields, and the new CLI options.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.15.0 — Mapping Profile Consolidation

Converter behavior is unchanged and test-proven: converting the example
corpus with the new registry produces byte-identical JSON-LD, mapping
reports, validation reports, and unmapped-field reports compared to
`mapping_v0_3.yaml`. Mapping catalog CSV, Web Vocabulary snapshots, and all
existing mapping YAML files are untouched.

- **One consolidated mapping artifact.** `mapping/mapping_registry.yaml`
  merges the executable mapping profile (structurally identical to
  `mapping_v0_3.yaml`) with the governance review catalog. Fields carry
  `governance` blocks (status, original catalog status, confidence, review
  flags) that the converter ignores; the full 29-row review catalog is
  preserved under a top-level `catalog` list. Statuses use a fixed vocabulary
  (proposed / review_required / accepted / rejected / deprecated / blocked);
  original catalog statuses are preserved verbatim as `catalog_status`.
  Generated deterministically by `scripts/build_mapping_registry.py`.
- **Old profiles archived, not deleted.** The sidebar now shows a calm
  "Active mapping profile" panel with a `Current` status badge; the registry
  is the default. `mapping_v0_3.yaml`, `mapping_v0_2.yaml`, and
  `mapping_mvp.yaml` remain on disk and selectable for reference/comparison
  only, inside an "Archived mapping profiles" expander; selecting one shows a
  visible warning and an `Archived` badge.
- **New registry loader.** `src/gdsn_to_gs1_jsonld/mapping_registry.py`
  exposes the governance view (per-field governance, catalog rows, summary
  counts) for review tooling; the converter keeps using the unchanged
  `mapping_loader`.
- **Design tokens & status badges.** `app/ui.py` gains a reusable status
  badge (current/accepted/review/blocked/archived) built on the existing
  semantic color tokens; badges always carry a text label (never color-only).
- **New policy test suites.** `tests/test_no_claims.py` asserts claim-shaped
  phrases (official GS1 validation, EU DPP compliance, production readiness)
  appear only in negated form across compliance-sensitive routes.
  `tests/test_no_dppk.py` asserts DPP Keystone terms/namespaces never appear
  in generated or recommended output (mapping, app, src, examples, builder
  manifest, product passport). `tests/test_mapping_registry.py` proves
  registry/converter equivalence and enforces the status vocabulary,
  including that no `hard_mapping_candidate` status exists.
- CI: the mapping-candidates smoke now uses the registry; a new
  `check-mapping` smoke guards registry/catalog consistency.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.14.0 — App Modularization

Strictly no user-facing behavior change: the converter, batch behavior,
single-file output, mapping YAML, mapping catalog, Web Vocabulary snapshots,
and every workflow's rendered output are all unchanged. All 197 tests
(including the 24 AppTest navigation/workflow tests) stay green.

- **`app/streamlit_app.py` split into `app/workflows/*.py` behind a thin
  router.** The single 2,500-line file is now a ~240-line router
  (`app/streamlit_app.py`) plus one module per workflow: `convert.py`,
  `explore.py`, `candidates.py`, `standards.py`, `prototype.py`,
  `product_passport.py`, `product_passport_builder.py`. Shared
  route/workflow-mode registry, session-state helpers, and sidebar loaders
  move to `app/workflow_shared.py`.
- **Enabler for lower-risk feature work.** Each workflow can now be read,
  tested, and changed in isolation instead of navigating one large file.
  First planned beneficiary: v0.15.0 browser-based visual smoke tests.
- Widget navigation in AppTest continues to select buttons by key
  (`route_<key>`, `workflow_mode_<key>`), so this refactor is invisible to the
  test suite by construction.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.13.5 — Release Hygiene & Test Environment Fix

Process and developer-environment maintenance only. No user-facing behavior
change: the converter, batch behavior, single-file output, mapping YAML, mapping
catalog, Web Vocabulary snapshots, the Streamlit workflows, and the Manual
Builder output are all unchanged.

- **Tighter release cadence, documented.** Adds this `## Unreleased` section and
  a "Release process" section to `docs/roadmap.md` so each meaningful change is
  tagged and released on its own, keeping "what is released" unambiguous.
- **Deterministic local test runs.** Tests now direct pytest's temporary-file
  root to a git-ignored, repo-local `.pytest-tmp` directory (via
  `tests/conftest.py`). This removes the ~34 `PermissionError: [WinError 5]`
  setup errors seen on machines whose default `pytest-of-<user>` temp directory
  is not writable; CI was already green and stays green. Full suite now reports
  `197 passed` locally with no errors.
- **Foundation-first roadmap.** `docs/roadmap.md` re-sequences the next feature
  releases (app modularization → visual smoke → Builder UX) ahead of the GS1 ↔
  Product Passport Crosswalk, which remains planned but moves behind the
  foundation work.

No warnings suppressed. No mock data. No fabricated coverage or compliance
claims. No official GS1 validation or production compliance is claimed.

## v0.13.4 — Workspace Polish & Manual Builder Coverage

Bundles the post-v0.13.3 workspace UI fixes and a large expansion of the Manual
JSON-LD Prototype Builder's property coverage. All changes are UI/config plus
the manual Builder serializer; the converter, batch behavior, single-file
output, mapping YAML, mapping catalog, and Web Vocabulary snapshots are
unchanged.

### Workspace UI

- Wider main workspace (~92rem via both the container hook and the stable
  `.block-container` class) so content fills the space next to the sidebar.
- Equal-height route and workflow cards (flex column pinning the outcome line);
  card-row buttons share a min-height.
- The active ("Active") button stays fully readable — Streamlit's disabled
  dimming is overridden with full opacity and white label text.

### Manual JSON-LD Builder — property coverage (~40 → 183 fields, 10 → 19 groups)

- **Breadth:** many more simple/"flat" `gs1:Product` / `gs1:FoodBeverageTobacco`
  fields — descriptions & marketing, consumer information, lifecycle dates,
  additional measurements, identifiers & variants, serving details, and
  consumer/DPP link types.
- **Nested objects:** a generic `object` input type; brand → `gs1:Brand`,
  image/referencedFile/instructions/handling/audio → `gs1:ReferencedFileDetails`,
  certification → `gs1:CertificationDetails`, packagingMaterial →
  `gs1:PackagingMaterial`, allergen → `gs1:AllergenDetails`.
- **Controlled codes:** a generic `code` input type emitting `{"@id": "gs1:…"}`;
  allergen types & containment, nutritional claim, preservation technique,
  growing method, source animal, packaging accreditation/free-from/diet-allergen,
  and more — all sourced from the local `webvoc/current` snapshot.
- **Nutrition:** all 43 per-nutrient measurements plus the nutrient basis
  quantity, emitted as `value` + `unitCode` quantities.

### Preserved

- Converter logic, batch behavior, and single-file output are unchanged.
- Mapping YAML, mapping catalog, and Web Vocabulary snapshots are unchanged.
- No warnings suppressed; no mock data; no fabricated coverage/compliance.
- All manual Builder output stays prototype and is not BMS/XPath traceable.
- No Crosswalk, SHACL execution, VC, or signed credentials. No official GS1
  validation or production compliance claimed.

## v0.13.3 — Guided Route Navigation

UI/UX navigation polish. No behaviour changes, no new features, no mock data,
no fabricated coverage or compliance claims.

### Changed

- **Two-stage guided route navigation.** The landing page now starts with three
  primary route cards instead of seven workflow cards:
  - **Create GS1 JSON-LD** → Convert GDSN XML, Create JSON-LD Prototype
  - **Vocabulary & Mapping** → Explore GS1 Web Vocabulary, Generate Mapping
    Candidates, Standards Review
  - **Product Passport Bridge** → Validate Product Passport Sources, Build
    Product Passport Prototype
- Selecting a route reveals only its child workflows (progressive disclosure)
  under a context heading ("Choose how to create JSON-LD", "Choose a review
  tool", "Choose a Product Passport tool").
- Route cards are visually heavier than child cards, with a clear active-state
  indicator and monospace route markers (JSON-LD / MAP / PASS).
- Default route is **Create GS1 JSON-LD**; **Convert GDSN XML** remains the
  default active workflow. Selecting a route opens its first child as the active
  workflow without clearing any conversion results.

### Preserved

- All seven workflows remain reachable; every workflow key is unchanged.
- Convert guided four-step flow, sidebar workspace status/context, compact hero,
  and the "Core conversion traceability" rail from v0.13.2 are preserved.
- Converter logic, batch behavior, and single-file output are unchanged.
- Mapping YAML, catalog data, and Web Vocabulary snapshots are unchanged.
- No warnings suppressed; no mock data; no fabricated coverage/compliance.
- No Crosswalk, SHACL execution, VC, or signed credentials. No official GS1
  validation or production compliance claimed.

## v0.13.2 — Workspace Layout & Theme Navigation Polish

UI/UX and information-architecture polish. No behaviour changes, no new
features, no mock data, no fabricated coverage or compliance claims.

### Changed

- **Wider workspace.** Main container max-width raised to ~82rem (≈1310px) so
  cards, JSON previews, mapping tables, and reports get more room without going
  full-bleed; long text stays constrained.
- **Sidebar reframed** as compact Workspace status / context: workspace status
  (version, mode, storage, warnings-visible), current context (mapping profile
  + active file), Sources (WebVoc snapshot, Product Passport schemas), and a
  Governance note. Supported-group chips moved into a collapsed expander.
- **Themed landing navigation.** The overview groups workflows under headings —
  Recommended path (Convert), Vocabulary & Mapping, JSON-LD Prototyping, and
  Product Passport Bridge — with Convert as the recommended starting point.
- **Shorter workflow-card copy** (one sentence + one outcome line each).
- **Clearer Product Passport distinction:** Validate Product Passport Sources
  (inspect sources/schemas/examples) vs Build Product Passport Prototype
  (wrap GS1 JSON-LD into a prototype envelope).
- **Traceability rail labelled** "Core conversion traceability" with a note that
  Product Passport workflows build on GS1 JSON-LD output as prototype/reference
  tooling — not an official traceability output.
- **Compacted hero** copy and badges (In-memory, BMS/XPath traceable,
  Review-only, Prototype Passport); privacy/trust messaging preserved.

### Preserved

- Converter logic, batch behavior, and single-file output are unchanged.
- Mapping YAML, catalog data, and Web Vocabulary snapshots are unchanged.
- All seven workflows remain reachable; every governance warning is preserved.
- No warnings suppressed, no mock data, no fabricated coverage/compliance.
- No Crosswalk, SHACL execution, VC, or signed credentials. No official GS1
  validation or production compliance claimed.

## v0.13.1 — Guided Convert Workflow

Patch release. Presents the Convert GDSN XML (Single XML) path as a guided
four-step flow with a progress indicator, wired to the real converter. No new
features, no mock data, no fabricated coverage or compliance claims.

### Changed

- Convert GDSN XML → Single XML is now a guided four-step flow with a progress
  indicator: Upload → Mapping → Validate → Export (colour-coded step accents).
- The flow uses the real converter/validator/reporter — the same outputs are
  produced and downloadable: product JSON-LD, mapping report XLSX, validation
  report JSON, and unmapped fields JSON.
- All seven workflows remain reachable; every governance warning is preserved;
  session persistence, "Clear results", and profile-change behaviour are
  unchanged.

### Added

- `app/ui.py` `render_convert_progress()` and progress/step styling.
- Progress-indicator regression test.

### Preserved

- Converter logic, batch behavior, and single-file output are unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots are unchanged.
- No warnings were suppressed. No mock data. No fabricated coverage or
  compliance claims.
- No GS1 ↔ Product Passport Crosswalk, SHACL execution, VC, or signed
  credentials were created.

## v0.13.0 — Product Passport Builder

Adds the Product Passport Builder in **minimal-schema prototype mode**. Wraps
GS1 Web Vocabulary JSON-LD (from the converter, the Manual JSON-LD Prototype
Builder, or pasted/uploaded input) into a prototype Product Passport JSON-LD
envelope and validates it against the committed built-in minimal schema.
Prototype/reference only. Structural validation only. Not official GS1
validation, not EU DPP regulatory compliance, and not production-ready.

### Added

- `src/gdsn_to_gs1_jsonld/product_passport_builder.py` — deterministic, offline
  builder: input loading/normalization, GTIN/name/brand extraction, envelope
  construction, validation (reusing the v0.12.x validator — no duplicated
  logic), summary, and output writers.
- `gdsn-to-gs1-jsonld build-product-passport` CLI command.
- "Build Product Passport Prototype" Streamlit workflow (marker: PB) with Input,
  Builder Settings, Product Passport Output, and Validation Report tabs. The
  overview grid is now a 4+3 layout for seven workflows.
- `product_passport/examples/gs1_product_for_passport_builder.jsonld` — a
  prototype/example GS1 JSON-LD input (not production data).
- `docs/product-passport-builder.md` and `docs/releases/v0.13.0.md`.
- `tests/test_product_passport_builder.py` and Streamlit tests for the new
  workflow.
- CI runs a `build-product-passport` smoke command.

### Notes

- Minimal-schema prototype mode only: the external DPP schemas in the source
  manifest remain placeholders and are not selectable build targets.
- Default output is deterministic; `generatedAt` is omitted unless explicitly
  supplied.

### Preserved

- Converter logic, batch behavior, and single-file output are unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots are unchanged.
- No warnings were suppressed.
- No GS1 ↔ Product Passport Crosswalk, SHACL execution, VC envelope, or signed
  credentials were created.
- No tag or release v0.13.0 was created.

## v0.12.1 — Product Passport Bridge Hardening

Hardening, consistency, CI, and UI/UX polish release. No new features; no
Product Passport Builder. Prototype/reference only; structural validation only;
no official GS1 validation or production compliance claimed.

### Changed

- Declared `jsonschema>=4` as an explicit project dependency (previously used
  but only present transitively). The required-field fallback validator is
  retained but now clearly labelled: validation reports carry a
  `validator_mode` (`jsonschema` or `minimal_fallback`), and CLI/UI surface a
  visible warning when the fallback path is used.
- Enforced the Product Passport source manifest against
  `source_manifest.schema.json` using jsonschema (Draft7) in addition to the
  existing custom domain checks (`source_id` pattern, `additionalProperties`).
- Refreshed the workflow-entry narrative so all six workflows are represented
  (Convert, Explore, Create JSON-LD Prototype, Generate Mapping Candidates,
  Validate Product Passport Sources, Standards Review).
- Product Passport Schema Validator: placeholder schemas with no downloaded
  file are no longer offered as selectable validation targets; they are listed
  as unavailable provenance placeholders. Validation status wording changed to
  "Structural schema check: Passed / Failed / could not be evaluated" to avoid
  implying regulatory or official compliance.
- CSV inventory output neutralizes spreadsheet formula injection (cells
  starting with `=`, `+`, `-`, `@`). JSON output is unchanged.
- Roadmap consolidated; duplicated/stale sections removed.

### CI

- CI now runs `python -m compileall app src` and a minimal CLI smoke matrix
  (Product Passport inventory, Product Passport validation, mapping candidate
  generation) in addition to `pytest`. Smoke commands write only to `/tmp`.

### Tests

- Added `tests/test_version_consistency.py` (pyproject / APP_VERSION /
  CHANGELOG / release notes / README must agree).
- Added `tests/test_product_passport_hardening.py` (jsonschema path, fallback
  warning, manifest schema enforcement, CSV injection neutralization).
- Added Streamlit tests for the six-workflow narrative and placeholder-schema
  handling.

### Preserved

- Converter logic, batch behavior, and single-file output remain unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- No Product Passport Builder, GS1 ↔ Product Passport Crosswalk, SHACL
  execution, or VC/signed-credential features were created.
- No tag or release v0.12.1 was created.

## v0.12.0 — Product Passport Source Import & Schema Validator

### Added

- Added `product_passport/` directory structure with reference source directories.
- Added `product_passport/reference_sources/source_manifest.json` with 7 source
  entries (contexts, JSON schemas, SHACL shapes, examples) for DPP reference
  tracking.
- Added `product_passport/reference_sources/source_manifest.schema.json`.
- Added `product_passport/examples/minimal_product_passport.json` — a minimal
  prototype Product Passport JSON-LD example for structural testing.
- Added `product_passport/reference_sources/raw_public/schemas/dpp_minimal.schema.json` —
  a minimal JSON Schema requiring `@context` and `@type`.
- Added `src/gdsn_to_gs1_jsonld/product_passport_sources.py` with source
  inventory, checksum verification, and JSON Schema structural validation
  functions.
- Added `gdsn-to-gs1-jsonld inventory-product-passport-sources` CLI command.
- Added `gdsn-to-gs1-jsonld validate-product-passport` CLI command.
- Added "Validate Product Passport Sources" Streamlit workflow card (marker: PP)
  with Source Inventory, Schema Validator, and Examples tabs.
- Added `docs/product-passport-bridge.md`.
- Added `docs/releases/v0.12.0.md`.
- Added `tests/test_product_passport_sources.py` with 14+ tests.
- Updated `app/ui.py`: `APP_VERSION = "v0.12.0"`.
- Updated README.md, CHANGELOG.md, roadmap, strategic-next-steps, UI_CHANGES.

### Preserved

- Converter logic, batch behavior, and single-file output remain unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- No Product Passport Builder was created.
- No GS1 ↔ Product Passport Crosswalk was created.
- No SHACL validation execution was implemented (shapes inventoried only).
- No VC/signed credentials were created.
- No online fetching or external API dependency was added.
- No tag or release v0.12.0 was created.

## v0.11.0 — Mapping Candidate Generator

### Added

- Added `src/gdsn_to_gs1_jsonld/mapping_candidate_generator.py` with
  deterministic offline scoring of (WebVoc property, GDSN attribute) pairs.
- Added `gdsn-to-gs1-jsonld generate-mapping-candidates` CLI command.
- Added "Generate Mapping Candidates" Streamlit workflow card (marker: MAP).
- Added `docs/mapping-candidate-generator.md`.
- Added v0.11.0 release notes.
- Added backend and Streamlit regression tests for the Mapping Candidate Generator.
- Updated `app/ui.py`: `APP_VERSION = "v0.11.0"`.

### Preserved

- Converter logic, batch behavior, and single-file output remain unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- No mappings are automatically accepted or written.
- No online fetching, external API dependency, or large dependency was added.
- No Product Passport or VC features were added.

## v0.10.0 — Manual JSON-LD Prototype Builder

### Added

- Added `builder_manifest/product_builder_v0_10.yaml` as UI/configuration for
  manual prototype authoring.
- Added manifest-driven manual-builder functions in
  `src/gdsn_to_gs1_jsonld/jsonld_builder.py`.
- Added the `Create JSON-LD Prototype` Streamlit workflow card.
- Added root class, product category, default language, thematic group,
  range-aware form fields, live JSON-LD preview, warnings, and JSON-LD download.
- Added explicit prototype/governance warning for manually entered output.
- Added `docs/manual-jsonld-builder.md` and v0.10.0 release notes.
- Added backend and Streamlit regression tests for the Builder.

### Preserved

- Converter logic, batch behavior, and single-file output remain unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- Mapping Candidate Generator was not created.
- No online fetching, external API dependency, or large dependency was added.

## v0.9.1 — Public Source Data Inventory & Reference Import

### Added

- Added `reference_data/source_manifest.json` and a lightweight source manifest
  schema for public GDSN and GS1 Web Vocabulary references.
- Added a public GDSN BMS/XPath 3.1.36 workbook copy under
  `reference_data/raw_public/`.
- Added normalized GDSN and WebVoc JSON/CSV reference outputs under
  `reference_data/normalized/`.
- Added `gdsn-to-gs1-jsonld import-reference-data`.
- Added offline importer tests for WebVoc BOM handling, class/property
  extraction, fake GDSN Excel normalization, candidate/deleted row flags,
  checksums, summary JSON, CLI outputs, and source-manifest schema coverage.
- Added `docs/source-data-inventory.md`, `docs/reference-data-import.md`, and
  v0.9.1 release notes.

### Preserved

- Converter logic, batch behavior, and single-file output remain unchanged.
- Mapping YAML files, catalog data, and existing Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- v0.10.0 Manual JSON-LD Prototype Builder and v0.11.0 Mapping Candidate
  Generator were not created.

## v0.9.0 — Web Vocabulary Explorer

### Added

- Replaced the Streamlit Web Vocabulary placeholder with a read-only Explorer.
- Added local WebVoc class/property extraction with labels, comments, domains,
  ranges, `subPropertyOf`, types, link-type indicators, and status metadata.
- Added property grouping, search, domain, group, coverage, mapped-only, and
  standards-review filters.
- Added mapping coverage statuses, BMS/XPath evidence, and SDR/governance
  indicators from existing local files.
- Added `gdsn-to-gs1-jsonld export-webvoc-explorer` with JSON, CSV, summary
  JSON, and summary XLSX outputs.
- Added `docs/webvoc-explorer.md` and v0.9.0 release notes.
- Added backend, CLI, helper, and Streamlit Explorer tests.

### Preserved

- Converter logic, batch behavior, and single-file output remain unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- No online fetching, external API dependency, or large dependency was added.

## v0.8.0 — Workflow Modes and Bulk XML Upload

### Added

- Added Streamlit workflow modes for `Convert GDSN XML`, `Explore GS1 Web
  Vocabulary`, and `Standards Review`.
- Moved the existing single-file conversion workflow into a `Single XML` tab.
- Added a `Bulk ZIP` tab for safe multi-file XML conversion from uploaded ZIPs.
- Added reusable batch conversion backend logic with XML discovery, non-XML
  ignoring, zip-slip protection, configurable limits, per-file continuation,
  summary JSON/XLSX, and downloadable batch export ZIPs.
- Added `gdsn-to-gs1-jsonld convert-batch`.
- Added a Web Vocabulary Explorer placeholder and compact read-only Standards
  Review mode.
- Added batch converter, CLI, and Streamlit workflow regression tests.
- Applied final UI/UX polish with a workspace posture panel, traceability rail,
  shorter `Open` / `Active` workflow actions, calmer container hierarchy, and
  subtle XML/VOC/SDR accents.

### Preserved

- Single-file converter output remains unchanged.
- Mapping YAML files, catalog data, and Web Vocabulary snapshots remain
  unchanged.
- No warnings were suppressed.
- No semantic mappings were changed.

### Validation

- pytest: 77 passed.
- compileall `app src`: passed.
- `git diff --check`: passed with only Windows LF/CRLF warnings.
- `convert-samples`: 4/4 successful.
- `check-catalog`: 0 errors, existing 8 warnings.
- `check-mapping`: 0 errors, existing 12 warnings.
- `convert-batch` sample ZIP: 4/4 successful.
- Streamlit startup probe: HTTP 200.
- GitHub Actions: success.

## v0.7.1 — Streamlit Cloud Import Fix

### Fixed

- Made `app/streamlit_app.py` import-safe with package-qualified `app.ui`
  imports.
- Added a `main()` guard for safer Streamlit startup.
- Added `app/__init__.py`.
- Added regression tests for Streamlit UI imports.
- Fixed CI-only import path handling in the regression tests.

### Preserved

- Converter output, mapping YAML files, and catalog data remain unchanged.
- No unresolved warning is suppressed or marked conformant.
- No semantic mappings were changed.
- No new dependencies were added.

### Validation

- pytest: 65 passed.
- compileall `app src`: passed.
- Streamlit startup probe: HTTP 200.
- `git diff --check`: passed with only Windows LF/CRLF warnings.
- GitHub Actions: success.

## v0.7.0 — Standards Review Backlog

### Added

- Six open standards decision records covering all 12 remaining warnings.
- Machine-readable JSON and CSV standards-review backlogs.
- Offline `export-standards-backlog` CLI command.
- Compact read-only standards backlog status in Streamlit.
- Tests for decision IDs, statuses, files, exports, and release-blocking flags.

### Preserved

- Converter output, mapping YAML files, and catalog data remain unchanged.
- No unresolved warning is suppressed or marked conformant.
- No new dependencies were added.

## v0.6.1 — Warning Cleanup and Conformance Notes

### Changed

- Reviewed all 15 v0.6.0 mapping warnings.
- Reclassified three structural parent-object false positives as informational
  findings, reducing `check-mapping` warnings from 15 to 12.
- Added `standards_review_required` and clearer evidence/actions to quality
  messages.
- Added explicit conformance notes for the 12 intentionally retained warnings.

### Preserved

- Converter output and mapping YAML semantics remain unchanged.
- `check-catalog` continues to report 0 errors and 8 non-blocking warnings.
- No new dependencies were added.

## v0.6.0 — Web Vocabulary Update Monitor & Conformance Hardening

### Added

- Controlled local snapshots of GS1 Web Vocabulary JSON-LD, Turtle, linktypes,
  and source metadata.
- `check-webvoc-updates` with online comparison, offline validation, JSON/Excel
  reporting, and explicit snapshot refresh.
- `revalidate-mapping-catalog` with JSON, Excel, and revalidated CSV outputs.
- Stable linktype recognition and structured warning classification.
- Compact local vocabulary status in Streamlit.

### Preserved

- Existing converter output, mapping YAML files, validation behavior, and CLI
  conversion behavior.
- Offline normal conversion with no external vocabulary fetch.
- Reviewable governance warnings where semantic decisions remain unresolved.

## v0.5.1 — Streamlit UI Polish

### Added

- Strategic positioning, governance, conformance, stakeholder, demo, and AI
  relevance documentation.
- A compact UI design direction, design-system reference, implementation plan,
  and UI change log.
- A premium Streamlit dashboard composition with a compact hero, conversion
  pipeline, workflow tiles, grouped sidebar, coverage badges, styled uploader,
  and polished empty state.
- A post-conversion review dashboard with output summary cards, validation and
  product identity cards, clearer previews, a 2x2 export grid, and review
  guidance.

### Changed

- Improved visual hierarchy, spacing, grouping, upload flow, result review, and
  export presentation.
- Preserved Streamlit session-state behavior and all existing download
  filenames, MIME types, and byte content.

### Preserved

- Converter, mapping, validation, and CLI behavior.
- Mapping YAML files, generated JSON-LD, generated reports, and dependencies.

### Validation

- pytest: 50 passed.
- compileall `app src`: passed.
- `git diff --check`: passed.
- Streamlit HTTP check: 200.
- GitHub Actions: success.

## v0.5.0 — Real-world GDSN Sample Robustness

### Added

- Four synthetic GDSN-like sample variants covering minimal, food,
  certification/document, and partially mapped products.
- `convert-samples` CLI command.
- JSON and Excel sample conversion summaries.
- Per-sample failure-stage and exception diagnostics.
- Unmapped-field context for language, nutrient, allergen, certification, and
  referenced-file discriminators.
- Sample corpus regression tests and sample-testing documentation.

### Preserved

- v0.1.0, v0.2.0, and v0.3.0 JSON-LD output compatibility.
- Existing mapping profiles and business mapping scope.
- Mapping catalog quality checks from v0.4.0.

### Notes / limitations

The sample files are synthetic and use fake identifiers and `example.com`
URLs. This release improves robustness and diagnostics; it does not add new
business mappings, full GDSN XSD validation, DPP expansion, Verifiable
Credentials, DCAT/DPROD, resolver calls, or certificate verification. An
unmapped-field finding is diagnostic and does not prove that XML is invalid.

## v0.4.0 — Mapping Catalog Driven Quality Checks

### Added

- Reusable catalog and YAML mapping quality checks.
- `check-catalog` and `check-mapping` CLI commands.
- Structured errors, warnings, and informational findings.
- JSON and multi-sheet Excel quality reports.
- Coverage, experimental mapping, review, and Web Vocabulary diagnostics.
- Tests and documentation for mapping governance workflows.

### Preserved

- v0.1.0, v0.2.0, and v0.3.0 converter output compatibility.
- Existing executable mapping YAML profiles.
- Shared converter package for CLI and Streamlit.

### Notes / limitations

This release checks existing governance data; it does not add business
mappings, generate YAML, verify certificates, dereference URLs, call resolvers,
implement Verifiable Credentials, add DCAT/DPROD, or provide full GDSN XSD
validation. Unknown catalog statuses and confidence values are warnings by
default and fail only in strict mode.

## v0.3.0 — BMS/XPath-aligned Certification & Document Mapping

### Added

- GDSN 3.1.36 BMS/XPath-aligned certification mapping.
- Certification and referenced-document canonical models.
- Experimental DPP-like and certification document links.
- `mapping/mapping_v0_3.yaml`.
- Mapping catalog governance, catalog documentation, and design documentation.
- Certifications & Documents v0.3.0 Streamlit profile.
- Compatibility, catalog, CLI, JSON-LD, and unmapped-report tests.

### Preserved

- v0.1.0 JSON-LD output with the MVP mapping.
- v0.2.0 JSON-LD output with the Food mapping.

### Notes / limitations

Certification mappings have stronger GS1 Web Vocabulary support than generic
document links. `gs1:referencedDocument` remains an experimental parent
relationship. No certificate verification, URL dereferencing, resolver calls,
Verifiable Credentials (VC), DCAT/DPROD, or full GDSN XSD validation is
included.

## v0.2.0 — Food Information Mapping

This release extends the GDSN to GS1 JSON-LD Converter with experimental
food/FMCG information mapping.

### Added

- Ingredient statement mapping with language support.
- Allergen details mapping.
- Basic nutrient detail mapping.
- Configurable nested `object_mappings`.
- New `mapping/mapping_v0_2.yaml`.
- Streamlit mapping profile selector with Food v0.2.0 as the default.
- Extended canonical product model for ingredients, allergens, and nutrients.
- Updated unmapped fields reporting for mapped food information.
- New expected v0.2.0 JSON-LD example output.
- Additional tests for the v0.2.0 mapping.

### Preserved

- The v0.1.0 mapping remains available.
- Existing v0.1.0 JSON-LD output remains unchanged when using the MVP mapping.
- CLI and Streamlit continue to use the same converter package.

### Supported fields

- GTIN
- Product name
- Product description
- Brand name
- GPC category code
- Net content value and unit
- Product image URL
- Product page URL
- Ingredient statement
- Allergen type and level of containment
- Nutrient type, preparation state, and quantity contained

### Notes / limitations

This is still an experimental converter. It does not yet provide full GDSN
coverage, full GDSN XSD validation, certification mapping, DPP document links,
batch processing, codelist enrichment, or Databricks integration.
