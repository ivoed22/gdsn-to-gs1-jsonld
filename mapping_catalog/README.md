# Mapping Catalog

The CSV mapping catalog is the standards traceability and governance layer for
this project. The YAML files under `mapping/` remain the executable converter
configuration.

The catalog links GDSN BMS IDs and official XPath expressions to canonical
fields, JSON-LD properties, mapping status, confidence, vocabulary validation,
and review actions.

Machine-readable governance inputs:

- `gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv`
- `gs1_webvoc_terms_used_in_mapping_catalog.csv`
- `gdsn_to_webvoc_mapping_review_issues.csv`

`GDSN_Attributes_with_BMSId_xPath_3.1.36_June_5_2026.xlsx` is the source
spreadsheet reference. Version 0.3.0 is the first converter release to use the
BMS/XPath and locally validated Web Vocabulary catalog as a design input.

Certification mappings have direct GS1 Web Vocabulary support for the parent,
object type, standard, value, and validity dates. Generic document-link
mappings remain experimental where no direct GS1 property exists.
