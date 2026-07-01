# Roadmap

All work is versioned in the v0.x series. The project is prototype/reference
tooling for standards discussion: it does not claim official GS1 validation or
production compliance, and it is not full GDSN coverage.

## Planned

### v0.14.0 — GS1 ↔ Product Passport Crosswalk (next feature release)

Map GS1 Web Vocabulary properties to Product Passport fields as review-only
crosswalk evidence. No automatic acceptance.

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
