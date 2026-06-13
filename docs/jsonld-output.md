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
