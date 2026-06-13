# Mapping profiles

`mapping/mapping_mvp.yaml` contains `metadata`, `settings`, and `fields`.
Each field declares its element-selecting XPath, value XPath, canonical target,
JSON-LD property, datatype, cardinality, requirement, language fallback, and
ordered transforms.

`mapping/mapping_v0_2.yaml` preserves those fields and adds:

- a language-string field for ingredient statements
- `object_mappings` for allergens and nutrients

An object mapping declares `parent_xpath`, `canonical_field`,
`jsonld_property`, optional `object_type`, cardinality, and relative child
fields. Child mappings can use dotted canonical and JSON-LD paths such as
`quantity_contained.value` and `gs1:quantityContained.value` to construct
nested measurements without hardcoding their property names in the extractor.

The mapping is the source of truth for emitted simple property names. For
language strings, select the XML element rather than `text()` in the main
XPath, then read text with `value_xpath` and language with `language_xpath`.

Supported transforms are `trim`, `normalize_whitespace`, `uppercase`,
`to_decimal`, `validate_gtin`, and `validate_url`.

The v0.1.0 profile remains available for output compatibility.
