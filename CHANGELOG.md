# Changelog

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
