# JSON-LD output

The output uses the GS1 Web Vocabulary context and a Schema.org prefix. A valid
GTIN becomes both `gs1:gtin` and the GS1 Digital Link identifier:

```json
{
  "@id": "https://id.gs1.org/01/08712345678906",
  "gs1:gtin": "08712345678906"
}
```

GTIN remains a string so leading zeroes are preserved. Product names and
descriptions are language-value arrays. Net content is emitted only when both
value and unit exist. Empty values are omitted and duplicate image URLs are
removed.

The Food v0.2.0 profile additionally emits:

- `gs1:ingredientStatement` as language-value arrays
- `gs1:hasAllergen` as `gs1:AllergenDetails` objects
- `gs1:nutrientDetail` with preparation state, nutrient type, and nested
  quantity

```json
{
  "gs1:nutrientDetail": [
    {
      "gs1:preparationStateCode": "UNPREPARED",
      "gs1:nutrientTypeCode": "ENER-",
      "gs1:quantityContained": {
        "value": 190,
        "unitCode": "KJO"
      }
    }
  ]
}
```

See `examples/output/expected_product_v0_2.jsonld` for the complete example.

The v0.3.0 profile adds `gs1:certification` objects and experimental referenced
documents:

```json
{
  "gs1:certification": [
    {
      "@type": "gs1:CertificationDetails",
      "gs1:certificationStandard": "EU Organic",
      "gs1:certificationValue": "Certified organic product"
    }
  ],
  "gs1:referencedDocument": [
    {
      "@type": "schema:DigitalDocument",
      "schema:additionalType": "DPP_DOCUMENT",
      "schema:url": "https://example.com/documents/08712345678906-dpp.pdf"
    }
  ]
}
```

`gs1:referencedDocument` is an experimental project mapping, not a term found
in the locally validated GS1 Web Vocabulary.
