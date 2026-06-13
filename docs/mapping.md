# Mapping profiles

`mapping/mapping_mvp.yaml` contains `metadata`, `settings`, and `fields`.
Each field declares its element-selecting XPath, value XPath, canonical target,
JSON-LD property, datatype, cardinality, requirement, language fallback, and
ordered transforms.

The mapping is the source of truth for emitted simple property names. For
language strings, select the XML element rather than `text()` in the main
XPath, then read text with `value_xpath` and language with `language_xpath`.

Supported transforms are `trim`, `normalize_whitespace`, `uppercase`,
`to_decimal`, `validate_gtin`, and `validate_url`.
