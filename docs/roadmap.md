# Roadmap

Version 0.11.0 adds the Mapping Candidate Generator, a deterministic offline
tool that proposes possible GDSN/BMS/XPath source fields for GS1 Web Vocabulary
properties with confidence scoring and review reasons.  Candidates are review
support only; no mappings are automatically accepted or written.

Version 0.10.0 added a Manual JSON-LD Prototype Builder on top of the v0.9.1
source-data inventory.

Potential work after v0.11.0:

- resolve catalog warnings through standards and project review
- connect manual JSON-LD prototypes to governed BMS/XPath evidence where
  appropriate
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

Version 0.9.1 adds `import-reference-data` and a committed source-data
inventory for public GDSN and Web Vocabulary references. It prepares normalized
evidence for future manual prototyping and mapping-candidate review without
building those features yet.

Version 0.11.0 adds the Mapping Candidate Generator: offline, deterministic,
review-only.  Candidates do not update YAML or converter output.

Version 0.10.0 adds manual JSON-LD prototype authoring. It is intentionally
separate from GDSN XML conversion and mapping YAML so manually entered examples
can be reviewed without changing governed converter output.

Potential work after v0.7.0:

- assign named reviewers and decision dates
- move reviewed records to Proposed, Accepted, Rejected, or Deferred
- create versioned mapping changes only for accepted decisions
- retain compatibility tests and migration notes for any accepted output change

## Strategic tracks after v0.11.0

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
