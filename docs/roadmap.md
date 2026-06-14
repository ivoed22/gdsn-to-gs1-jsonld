# Roadmap

Version 0.5.0 adds realistic synthetic sample coverage, sample-level
diagnostics, and richer unmapped context while preserving the v0.1.0, v0.2.0,
and v0.3.0 converter profiles and output.

Potential work after v0.5.0:

- resolve catalog warnings through standards and project review
- broader GDSN modules and mapping profiles
- richer ingredients, allergens, serving sizes, and nutrition
- standards review for generic document-link relationships
- certificate verification and richer certification agency modeling
- optional GDSN XSD validation
- production-oriented batch processing and diagnostic aggregation
- API and data-platform integrations

The current release is still not full GDSN coverage.

## Strategic tracks after v0.5.0

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
