# Roadmap

All work is versioned in the v0.x series. The project is prototype/reference
tooling for standards discussion: it does not claim official GS1 validation or
production compliance, and it is not full GDSN coverage.

## Release process

Each version lands as one CI-gated commit on main with its own CHANGELOG
heading and `docs/releases/vX.Y.Z.md`, so "what is released" stays
unambiguous.

- Work in progress accumulates under `## Unreleased` in `CHANGELOG.md`.
- A version commit renames that section to its `vX.Y.Z` heading, adds
  `docs/releases/vX.Y.Z.md`, and bumps the version in `pyproject.toml`, the
  `app/ui.py` `APP_VERSION`, and the README. `tests/test_version_consistency.py`
  enforces these stay in sync.
- Annotated tags and GitHub Releases are created only when explicitly
  requested, and only after CI is green on the version commit.

## Planned (GS1-first DPP workbench, foundation-first)

The direction is a GS1-first Digital Product Passport and JSON-LD standards
workbench. DPP Keystone is tooling-pattern inspiration only and is never a
semantic authority: generated/recommended output must not contain dppk terms
(no-dppk policy, test-enforced since v0.15.0). The near-term sequence
prioritises the mapping foundation and UX/test hardening before the
Crosswalk.

### v0.22.0+ — GS1-first DPP Crosswalk (deferred behind foundation)

Map DPP fields to GS1-first semantics (GS1 Web Vocabulary → GS1 Digital
Link → CIRPASS/DPP core → sector vocabularies → schema.org fallback → local
extension) as review-only crosswalk evidence with explicit source priority.
No automatic acceptance. Broader DPP toolkit modules (JSON-LD Reviewer, DPP
Wizard, CSV DPP Adapter, Coverage Dashboard) phase in afterwards as
separately scoped versions. **Blocked** on sourcing specific CIRPASS/
CIRPASS-2/sector-vocabulary versions as pinned local sources — the user is
researching how to retrieve these; this project does not fetch online or
guess source URLs.

### Later (still v0.x)

- SHACL shape execution against prototype Product Passport data.
- GS1 Digital Link / EPCIS publication previews.
- Verifiable Credentials / trust layer (envelope and proofs).
- Resolve catalog warnings through standards and project review.
- Connect manual JSON-LD prototypes to governed BMS/XPath evidence where
  appropriate.
- Broader GDSN modules and mapping profiles; richer ingredients, allergens,
  serving sizes, and nutrition.
- Standards review for generic document-link relationships; richer
  certification modelling.
- Optional GDSN XSD validation.
- Operational batch processing beyond ZIP upload and diagnostic aggregation.
- API and data-platform integrations.

### Standards-review workflow (future)

- Assign named reviewers and decision dates.
- Move reviewed records to Proposed, Accepted, Rejected, or Deferred.
- Create versioned mapping changes only for accepted decisions.
- Retain compatibility tests and migration notes for any accepted output change.

## Released

- **v0.24.0 — Offline vocabulary freshness check.** Surfaces the
  previously CLI-only `check-webvoc-updates` capability in the UI, built
  on a new `compare_webvoc_snapshot_bytes` function with no network code
  path at all (unlike the CLI command, which can optionally fetch GS1's
  live URLs). Standards Review gains a section where a reviewer uploads a
  candidate `gs1Voc.jsonld` and sees new/removed/changed terms against the
  pinned local snapshot. Diagnostic only; never writes to governed data.
- **v0.23.0 — Full WebVoc codelist option in Manual Builder.** Corrected
  course after investigation: the originally planned "6 codelist_pending
  fields" premise didn't hold (all already had options, weren't
  authorable as `code` fields, or already had a complete curated set).
  The one verified gap — `gs1:allergenType`'s 14-value EU subset versus
  WebVoc's 385 defined `AllergenTypeCode` individuals — got a "show full
  code list" checkbox via a new generic `webvoc_explorer.
  group_individuals_by_class`, keyed off each property's own WebVoc range
  class. Default behavior unchanged; no fabricated values.
- **v0.22.0 — Bulk ZIP codelist validation.** Extends v0.21.0's codelist
  validation panel to the Bulk ZIP workflow: `convert_batch_zip` gains the
  same fully opt-in `codelist_registry` parameter, and the workflow shows
  an aggregate status-count panel plus a per-file issue table after batch
  conversion. No converter/batch behavior change; batch success/failure
  counts and the export ZIP are unaffected.
- **v0.21.0 — Codelist validation UI (Track D UI wiring).** Convert GDSN
  XML's Review-mapping step gains a read-only codelist validation panel
  (status counts, table, per-entry detail with a status badge). No
  converter behavior change; still exactly 4 downloads.
- **v0.20.0 — Codelist import & enforcement (Track D).** User-provided
  official public GDSN and Shared Common Code Lists workbook (595
  codelists, 14,564 values) imported into a committed, deterministic
  registry (`codelist_importer.py`). New `codelist_registry.py` validates
  codelist-backed fields (valid/unknown/deprecated/missing/
  source_unavailable) against a curated, independently verified
  field-to-codelist table. `convert_xml_to_jsonld` gains a fully opt-in
  `codelist_registry` parameter — default `None` is byte-identical to every
  prior version; passing a registry only adds a diagnostic
  `codelist_validation` list, never blocking conversion.
- **v0.19.0 — Builder manifest expansion analysis (Track C).** Read-only
  "Builder Manifest Expansion Analysis" workflow classifies the 371
  not-yet-authorable WebVoc properties into `ready_now` /
  `needs_codelist_curation` / `needs_hard_mapping_review` /
  `not_ready_no_evidence`, using the mapping registry catalog and Track B's
  hard-mapping detection. DPP relevance is reported as not-yet-assessed for
  every candidate (the Crosswalk's job, now v0.22.0+). No automatic
  manifest expansion.
- **v0.18.0 — Builder UX at scale.** Coverage overview across manifest
  groups, per-field status chips (`builder_status.py`, reusing Track B's
  hard-mapping detection), search/filter, evidence expanders, clearer
  export area. Fixes controlled-vocabulary (`code`) fields that silently
  showed no real options. Serializer/validator/state model unchanged.
- **v0.17.0 — Visual smoke tests.** Browser-based smoke
  (`scripts/visual_smoke.py`, Playwright + Chromium) walks the landing page
  and all seven workflows, asserting no viewport overflow, readable active
  buttons, visible warnings, and no compliance claims without negation. No
  app behavior changes; non-blocking CI job while it stabilizes.
- **v0.16.0 — Full-scope mapping scoring & promotion lanes (Track B).**
  Every candidate carries a deterministic `hard_mapping` flag and
  `review_lane`; both lanes reach the same `accepted` terminal status via
  `mapping_promotion.py` (standard: score → review → accepted; hard-mapping:
  score → dedicated extra review sign-off → accepted). `--full-scope` scores
  all 553 WebVoc properties against the full ~6,067-attribute GDSN
  reference (~7 min; local/offline, not in CI). Review-only throughout; no
  mapping YAML/registry/catalog is written automatically.
- **v0.15.0 — Mapping profile consolidation (Track A).** One authoritative
  artifact, `mapping/mapping_registry.yaml`, merges the executable mapping
  profile with the governance review catalog; old profiles archived (kept on
  disk, reference/comparison only, behind a warning). Converter output
  unchanged, test-proven byte-identical. Adds no-claim and no-dppk policy
  test suites and the reusable status-badge design tokens.
- **v0.14.0 — App modularization.** Splits the large `app/streamlit_app.py`
  into `app/workflow_shared.py` and `app/workflows/*.py` behind a thin
  router. Strictly no behavior change; all 197 tests, including navigation
  tests, stay green. Enabler for faster, lower-risk feature work — starting
  with v0.15.0.
- **v0.13.0 — Product Passport Builder.** Wraps GS1 Web Vocabulary JSON-LD into
  a prototype Product Passport JSON-LD envelope in minimal-schema prototype
  mode, validated against the committed built-in minimal schema. Prototype/
  reference only; structural validation only; not official GS1 validation, not
  EU DPP regulatory compliance, and not production-ready.
- **v0.12.1 — Product Passport Bridge Hardening.** `jsonschema` declared as an
  explicit dependency with a flagged fallback; source manifest enforced against
  its JSON Schema; six-workflow narrative; placeholder schemas not selectable;
  structural-check wording; CI runs compileall and a CLI smoke matrix.
- **v0.12.0 — Product Passport Bridge.** Inventory public DPP reference sources
  and validate prototype Product Passport JSON against local JSON Schemas.
  Source inventory and structural schema validation only. SHACL execution,
  Product Passport Builder, and the GS1 ↔ Product Passport Crosswalk are not
  built.
- **v0.11.0 — Mapping Candidate Generator.** Deterministic, offline tool that
  proposes possible GDSN/BMS/XPath source fields for GS1 Web Vocabulary
  properties with confidence scoring and review reasons. Review-only; no
  mappings are automatically accepted or written.
- **v0.10.0 — Manual JSON-LD Prototype Builder.** Manual prototype authoring,
  intentionally separate from GDSN XML conversion and mapping YAML so manually
  entered examples can be reviewed without changing governed converter output.
- **v0.9.1 — Public source-data inventory & reference import.** Adds
  `import-reference-data` and a committed source-data inventory for public GDSN
  and Web Vocabulary references. Prepares normalized evidence for later manual
  prototyping and mapping-candidate review without building those features.
- **v0.9.0 — Web Vocabulary Explorer.** Replaces the Explorer placeholder with a
  real offline Explorer and `export-webvoc-explorer` CLI command. Read-only
  standards/mapping review; not a converter-output or mapping-semantics change.
- **v0.8.0 — Workflow modes & Bulk ZIP.** Introduces Streamlit workflow modes,
  keeps the single-XML path unchanged, adds a Bulk ZIP tab and a `convert-batch`
  CLI command. Operational workflow release, not a mapping-semantics release.
- **v0.7.0 — Standards decisions.** Organizes conformance/governance warnings
  into six open standards decisions rather than changing mappings to reduce
  counts.
- **v0.6.1 — Warning triage.** Separates tooling false positives from 12 genuine
  conformance and governance warnings.

## Strategic tracks

### Positioning and demo

Use the implemented pipeline and synthetic sample corpus to explain how GDSN,
BMS/XPath traceability, GTIN, and GS1 Web Vocabulary can connect product-data
exchange to machine-readable structured data for AI and digital ecosystems.

### Web Vocabulary conformance hardening

Resolve current vocabulary warnings, clarify nutrient and certification
semantics, decide the generic document/DPP link pattern, and establish
terminology and evidence for aligned versus conformant output.

### Real-world input diagnostics

Continue testing sanitized real-world GDSN variants, improve failure
classification, and aggregate recurring unmapped structures without treating
every source element as new mapping scope.

### Catalog-to-YAML generation

Consider generating executable YAML from an authoritative mapping catalog as a
later option, after decisions on mapping authority, status vocabulary,
versioning, and review workflow.
