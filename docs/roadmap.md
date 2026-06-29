# Roadmap

Version 0.9.0 adds a read-only Web Vocabulary Explorer on top of the v0.8.0
workflow modes. The Explorer browses the local GS1 Web Vocabulary snapshot and
compares properties with mapping catalog coverage, BMS/XPath evidence, and SDR
governance indicators while preserving the v0.1.0, v0.2.0, and v0.3.0
converter profiles and single-file output.

Potential work after v0.9.0:

- resolve catalog warnings through standards and project review
- prototype manual JSON-LD authoring only when it can be linked to mapping
  evidence and clear governance
- broader GDSN modules and mapping profiles
- richer ingredients, allergens, serving sizes, and nutrition
- standards review for generic document-link relationships
- certificate verification and richer certification agency modeling
- optional GDSN XSD validation
- production-oriented batch processing beyond ZIP upload and diagnostic aggregation
- API and data-platform integrations

The current release is still not full GDSN coverage.

Version 0.6.1 separates tooling false positives from 12 genuine conformance
and governance warnings. Version 0.7.0 organizes those warnings into six open
standards decisions rather than changing semantic mappings solely to reduce
counts.

Version 0.8.0 introduces workflow modes in Streamlit, keeps the single XML path
unchanged, adds a Bulk ZIP tab, and adds a `convert-batch` CLI command. It is
an operational workflow release, not a mapping semantics release.

Version 0.9.0 replaces the Web Vocabulary Explorer placeholder with a real
offline Explorer and `export-webvoc-explorer` CLI command. It is a read-only
standards/mapping review release, not a converter-output or mapping-semantics
release.

Potential work after v0.7.0:

- assign named reviewers and decision dates
- move reviewed records to Proposed, Accepted, Rejected, or Deferred
- create versioned mapping changes only for accepted decisions
- retain compatibility tests and migration notes for any accepted output change

## Strategic tracks after v0.9.0

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
later option. This should follow decisions on mapping authority, status
vocabulary, versioning, and review workflow rather than precede them.
