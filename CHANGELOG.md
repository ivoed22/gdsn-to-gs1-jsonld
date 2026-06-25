# Changelog

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
