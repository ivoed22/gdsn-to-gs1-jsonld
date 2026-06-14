# Before and After

This simplified example shows the practical transformation from GDSN-like XML
to GS1 Web Vocabulary JSON-LD. It is illustrative rather than a complete GDSN
message or conformance example.

## Before: exchange-oriented XML

```xml
<tradeItem>
  <gtin>95012345678903</gtin>
  <tradeItemDescription languageCode="en">
    Minimal Test Product
  </tradeItemDescription>
  <brandName>Example Minimal</brandName>
  <netContent>
    <measurementValue>1</measurementValue>
    <measurementUnitCode>KGM</measurementUnitCode>
  </netContent>
</tradeItem>
```

The values are structured, but their meaning depends on the source message,
namespaces, hierarchy, and GDSN definitions.

## After: web-native JSON-LD

```json
{
  "@context": {
    "gs1": "https://gs1.org/voc/",
    "schema": "https://schema.org/"
  },
  "@type": "gs1:Product",
  "@id": "https://id.gs1.org/01/95012345678903",
  "gs1:gtin": "95012345678903",
  "gs1:productName": {
    "@value": "Minimal Test Product",
    "@language": "en"
  },
  "gs1:brandName": "Example Minimal",
  "gs1:netContent": {
    "value": 1,
    "unitCode": "KGM"
  }
}
```

## What changed

### XML exchange structure became web-native structured data

The nested source message became a compact JSON-LD product resource. Consumers
can use explicit properties without reproducing the XML extraction logic.

### GTIN became a GS1 Digital Link-style URI

The GTIN remains available as `gs1:gtin` and also forms the product `@id`:
`https://id.gs1.org/01/95012345678903`. This gives the product a globally
meaningful web identifier pattern.

### GDSN fields became GS1 Web Vocabulary properties

The description, brand, and net content are expressed using target vocabulary
properties. Language and quantity structure are retained where the mapping
requires them.

### Mapping remained traceable to BMS/XPath

The transformation is backed by a versioned mapping profile and catalog. The
catalog can record the BMS identifier, official XPath, canonical field, target
property, confidence, and review status for each rule.

| Source concept | Canonical field | JSON-LD property |
| --- | --- | --- |
| GTIN | `gtin` | `gs1:gtin` |
| Trade item description | `product_name` | `gs1:productName` |
| Brand name | `brand_name` | `gs1:brandName` |
| Net content value and unit | `net_content_value`, `net_content_unit` | `gs1:netContent` |

This traceability supports review, but it does not by itself prove source-data
truth, full GDSN validation, or complete GS1 Web Vocabulary conformance.
