# Mapping profiles

`mapping/mapping_mvp.yaml` contains `metadata`, `settings`, and `fields`.
Each field declares its element-selecting XPath, value XPath, canonical target,
JSON-LD property, datatype, cardinality, requirement, language fallback, and
ordered transforms.

`mapping/mapping_v0_2.yaml` preserves those fields and adds:

- a language-string field for ingredient statements
- `object_mappings` for allergens and nutrients

`mapping/mapping_v0_3.yaml` preserves v0.2.0 and adds catalog-governed object
mappings for certifications and referenced documents. See
[`mapping-catalog.md`](mapping-catalog.md) for traceability and
[`v0.3.0-design.md`](v0.3.0-design.md) for experimental decisions.

An object mapping declares `parent_xpath`, `canonical_field`,
`jsonld_property`, optional `object_type`, cardinality, and relative child
fields. Child mappings can use dotted canonical and JSON-LD paths such as
`quantity_contained.value` and `gs1:quantityContained.value` to construct
nested measurements without hardcoding their property names in the extractor.

The mapping is the source of truth for emitted simple property names. For
language strings, select the XML element rather than `text()` in the main
XPath, then read text with `value_xpath` and language with `language_xpath`.

Supported transforms are `trim`, `normalize_whitespace`, `uppercase`,
`to_decimal`, `to_date`, `validate_gtin`, and `validate_url`.

The v0.1.0 and v0.2.0 profiles remain available for output compatibility.

## Catalog alignment

Version 0.4.0 can flatten simple fields, object mappings, and object child
fields from any profile for comparison with the mapping catalog:

```bash
gdsn-to-gs1-jsonld check-mapping \
  --mapping mapping/mapping_v0_3.yaml \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --output mapping_quality_report/
```

The check reports missing canonical fields, property differences,
high-confidence catalog coverage, experimental mappings, and review items. It
does not modify the mapping file or converter output.

## Testing profiles against samples

Version 0.5.0 adds `convert-samples` for applying an existing mapping profile
to every XML file in a directory:

```bash
gdsn-to-gs1-jsonld convert-samples \
  --input-dir examples/input/samples \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir examples/output/samples
```

This workflow tests extraction robustness and diagnostics; it does not infer
new mappings from sample XML. Elements in an unmapped report remain candidates
for review rather than automatically becoming mapping requirements.
