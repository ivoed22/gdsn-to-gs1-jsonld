# Changelog

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
