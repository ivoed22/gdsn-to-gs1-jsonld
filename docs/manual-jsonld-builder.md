# Manual JSON-LD Prototype Builder

Version v0.10.0 adds a manual JSON-LD prototype workflow to the Streamlit app.
It lets a user select GS1 Web Vocabulary properties, enter values, and preview
JSON-LD live.

This is prototype authoring, not GDSN XML conversion.

## Property coverage

The Builder exposes a curated subset of the ~553 GS1 Web Vocabulary properties,
limited to **simple ("flat") ranges** the Builder can emit safely: text,
language-tagged text (`rdf:langString`), URL/link types (`xsd:anyURI`),
`xsd:date`/`xsd:dateTime`, `xsd:boolean`, numeric (`xsd:integer`/`decimal`), and
`gs1:QuantitativeValue` (value + unitCode).

The manifest (`builder_manifest/product_builder_v0_10.yaml`) now covers 88 fields
across 14 thematic groups. Beyond the original core set it adds Product
descriptions & marketing, consumer information (instructions, safety, recall),
lifecycle dates, and consumer/DPP link types.

Properties whose range is a **nested object** (e.g. `gs1:Brand`,
`gs1:ReferencedFileDetails`, certification / allergen / packaging / nutrient
objects) remain flagged `supported_in_v0_10: false` and are shown as *planned*
until safe object modelling is added. This is a UI/config manifest only — it is
not converter mapping YAML and does not change governed converter output.

## Purpose

The Builder helps standards and product-data reviewers explore what GS1 Web
Vocabulary product markup could look like before a governed GDSN mapping exists.

It is useful for:

- testing Web Vocabulary property choices
- reviewing range-aware input behaviour
- discussing DPP, certification, packaging, allergen, and nutrition modelling
- creating a copyable JSON-LD prototype for review

## How It Differs From Conversion

The GDSN XML converter reads XML, applies versioned mapping YAML, and produces
mapping, validation, and unmapped-field evidence.

The Manual JSON-LD Builder does none of that. It accepts manually entered
values and generates a prototype JSON-LD preview. The output is not BMS/XPath
traceable unless it is separately linked to governed mapping evidence.

## How It Differs From The Explorer

The Web Vocabulary Explorer is read-only. It shows local WebVoc classes,
properties, ranges, coverage status, BMS/XPath evidence, and SDR indicators.

The Builder is an authoring surface. It uses local WebVoc metadata and the
builder manifest to decide which fields can be edited and how they should be
serialized.

## Supported Root Class

v0.10.0 supports:

- `Product`

The generated JSON-LD uses:

```json
"@type": "Product"
```

## Manifest-Driven Layout

The form layout is controlled by:

```text
builder_manifest/product_builder_v0_10.yaml
```

This file is UI configuration. It is not converter mapping logic and must not
be used to generate or update mapping YAML.

The manifest defines:

- root classes
- product categories
- thematic groups
- property display order
- required/recommended/optional flags
- input type overrides
- example values
- help text
- v0.10 support flags
- planned reasons for unsupported fields

## Field Groups

v0.10.0 includes these groups:

- Core Product Information
- Classification & Links
- Physical Dimensions
- Digital Links & Services
- Packaging Details
- Nutritional Information
- Allergens
- Certifications
- Documents and DPP
- Other Web Vocabulary Properties

## Range-Aware Inputs

The Builder infers input widgets from Web Vocabulary range metadata:

- `xsd:string`: text
- `rdf:langString`: text plus language tag
- `xsd:boolean`: checkbox
- `xsd:integer`: integer
- `xsd:float` / `xsd:decimal`: number
- `xsd:date`: date
- `xsd:dateTime`: date/time
- `xsd:anyURI`: URL text
- `gs1:QuantitativeValue`: value plus `unitCode`

Nested object ranges such as `gs1:Brand`, `gs1:CertificationDetails`,
`gs1:AllergenDetails`, and `gs1:ReferencedFileDetails` are shown as planned
where relevant and are not emitted as malformed scalar JSON-LD.

## JSON-LD Output

The generated output uses the current project context convention:

```json
"@context": [
  "https://ref.gs1.org/voc/data/gs1Voc.jsonld",
  {
    "schema": "https://schema.org/"
  }
]
```

If `gs1:gtin` is entered, the Builder generates:

```json
"@id": "https://id.gs1.org/01/{gtin}"
```

Properties are emitted with compact names without the `gs1:` prefix, for
example:

```json
{
  "@type": "Product",
  "gtin": "09501234567890",
  "productName": [
    {
      "@language": "en",
      "@value": "Example apple juice"
    }
  ]
}
```

Empty fields are omitted.

## Language-Tagged Values

Language-tagged values are emitted as arrays:

```json
"productName": [
  {
    "@language": "en",
    "@value": "Example apple juice"
  }
]
```

The Streamlit UI provides a default language selector with:

- `en`
- `nl`
- `de`
- `fr`

## Quantity Handling

Quantity-like properties are emitted only when both value and `unitCode` are
present:

```json
"netContent": {
  "value": 1,
  "unitCode": "LTR"
}
```

If a value is entered without a unit, or a unit is entered without a value, the
Builder shows a validation warning and does not emit malformed quantity data.

## Prototype Warning

The Builder always shows this warning:

> Manual JSON-LD prototype. This output is entered manually, not generated from
> GDSN XML. It is not BMS/XPath traceable unless linked to governed mapping
> evidence. It is not an official GS1 validation result.

## Limitations

v0.10.0 does not:

- convert GDSN XML through the Builder
- write mapping YAML
- update the mapping catalog
- update Web Vocabulary snapshots
- build the Mapping Candidate Generator
- model nested WebVoc objects for Brand, Certification, Allergen, Nutrient, or
  ReferencedFile details
- perform official GS1 validation
- fetch online resources

The Builder is intentionally a manual review and prototyping tool.
