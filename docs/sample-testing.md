# Testing with GDSN XML samples

Version 0.5.0 provides a small synthetic corpus for testing realistic
GDSN-like structures without using company or production data.

## Included samples

- `minimal_product.xml`: required identity plus brand and net content
- `food_product_full.xml`: descriptions, ingredients, allergens, and nutrients
- `certified_product_with_documents.xml`: certification, certificate link, and
  DPP-like document link
- `partially_mapped_product.xml`: valid mapped core fields plus intentionally
  unmapped metadata

All identifiers are fake and all URLs use `example.com`.

## Convert the corpus

```bash
gdsn-to-gs1-jsonld convert-samples \
  --input-dir examples/input/samples \
  --mapping mapping/mapping_v0_3.yaml \
  --output-dir examples/output/samples
```

Each sample produces product JSON-LD, a mapping workbook, a validation report,
and an unmapped report. The output directory also receives:

- `sample_conversion_summary.json`
- `sample_conversion_summary.xlsx`

The summary records the sample filename, detected GTIN, conversion and
validation status, output filename, validation counts, unmapped counts, mapped
field count, failure stage, exception message, and notes.

Failure stages distinguish mapping loading, XML parsing, conversion/validation,
and output writing. Errors are printed by the CLI and retained in the summary;
they are not silently skipped.

## Test private real-world files

Create a local directory outside the committed sample corpus and place copies
of real GDSN XML files there. Then run the same command with that directory as
`--input-dir`. Do not commit production XML or generated reports unless the
data has been reviewed and sanitized.

The parser disables entity resolution and network access, but the converter
does not perform full GDSN XSD validation. A successful conversion means the
selected profile could extract and validate its required canonical fields; it
does not certify complete GDSN conformance.

## Interpreting unmapped fields

The unmapped report lists populated XML elements that were not consumed by the
selected mapping. Repeated structures include context when available:

- `languageCode`
- `referencedFileTypeCode`
- `nutrientTypeCode`
- `allergenTypeCode`
- `certificationIdentification`

An unmapped element may be intentionally out of scope, supporting metadata, or
a candidate for future standards review. Its presence is not proof that the
input XML is invalid.
