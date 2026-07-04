# Manual JSON-LD Prototype Builder

Version v0.10.0 adds a manual JSON-LD prototype workflow to the Streamlit app.
It lets a user select GS1 Web Vocabulary properties, enter values, and preview
JSON-LD live.

This is prototype authoring, not GDSN XML conversion.

## v0.23.0 — Full WebVoc codelist option

`gs1:allergenType`'s manifest options were a hand-curated 14-value EU
subset of the 385 individuals the local Web Vocabulary snapshot actually
defines for `gs1:AllergenTypeCode`. The field now shows a "Show full code
list (385 total) instead of the curated 14" checkbox; checking it swaps
the dropdown to the full, real WebVoc-defined set (default view is
unchanged). The mechanism (`webvoc_explorer.group_individuals_by_class`)
is generic — keyed off each property's own WebVoc `range` class, not a
per-field table — so it applies automatically to any current or future
`code`-type field where the manifest's curated subset is smaller than
what WebVoc actually defines. See `docs/releases/v0.23.0.md` for what was
checked and found not to need a change (`allergenLevelOfContainmentCode`
already has its full 3-value set; several other candidate fields aren't
authorable `code`-type fields yet).

## v0.18.0 — Builder UX at scale

With the manifest at 183 fields across 19 groups, the Builder gained
navigation and status aids so a reviewer can work at that scale without
losing track of what's filled, missing, or flagged:

- **Coverage overview.** A table across every group in the selected product
  category (field count, filled, missing-required, flagged-for-review),
  computed from the same persisted values as the live preview, so switching
  groups doesn't lose sight of the rest of the form.
- **Per-field status chip.** Every field header shows a status badge —
  `Filled`, `Missing (required)`, `Review required`, `Hard-mapping review`,
  `Codelist pending`, `Blocked`, or `Not filled` — derived by
  `src/gdsn_to_gs1_jsonld/builder_status.py` (pure functions, unit-tested,
  no change to the serializer). Two vocabulary values,
  `external_source_required` and `extension_candidate`, are reserved and
  never triggered today — they need data that doesn't exist yet (a promoted
  hard mapping; a Crosswalk gap), and this project does not fabricate data
  to fill a status.
- **Hard-mapping review status.** Reuses the exact same deterministic
  detection rules as the v0.16.0 Mapping Candidate Generator
  (`detect_hard_mapping`), applied to whatever GDSN evidence is already
  linked to a WebVoc property, so a field backed by a cross-reference
  (organization/party, country, cross-item product reference) is visibly
  flagged for extra review before it's treated as routine.
- **Search and status filter.** A text search (label/property/help text) and
  a status multiselect narrow the current group's fields without touching
  which group is selected or the underlying state.
- **Evidence expander.** Each field with catalog evidence gets an expander
  showing the GDSN attribute name, BMS ID, XPath, mapping status, and
  confidence — the same evidence data the header's "N mapping evidence
  row(s)" hint already summarized, now inspectable.
- **Clearer export area.** The download/clear controls now sit under an
  explicit "Export" section with the current group's fill/missing/flagged
  counts shown alongside the download button.
- **Bug fix: controlled-vocabulary (`code`) fields now show their real
  options.** Before v0.18.0, every `code`-type field's dropdown silently
  showed only the "— none —" placeholder — the manifest's per-field
  `options` list was parsed but never threaded through to the render layer.
  Fields like `gs1:packagingMarkedLabelAccreditation` (30+ real controlled
  values) were effectively unusable. Fixed by carrying `options` through
  `_property_metadata_index`; regression-tested.

The manual builder's state model, serializer (`serialize_builder_state_to_jsonld`),
and validator (`validate_builder_state`) are unchanged — status derivation
reads the same persisted values, it does not compute or store anything new
in builder state.

## Property coverage

The Builder exposes a curated subset of the ~553 GS1 Web Vocabulary properties,
limited to **simple ("flat") ranges** the Builder can emit safely: text,
language-tagged text (`rdf:langString`), URL/link types (`xsd:anyURI`),
`xsd:date`/`xsd:dateTime`, `xsd:boolean`, numeric (`xsd:integer`/`decimal`), and
`gs1:QuantitativeValue` (value + unitCode).

The manifest (`builder_manifest/product_builder_v0_10.yaml`) now covers 183
fields across 19 thematic groups — the large majority of the safely-authorable
`gs1:Product` / `gs1:FoodBeverageTobaccoProduct` properties. Beyond the original
core set it adds Product descriptions & marketing, consumer information,
lifecycle dates, additional measurements, identifiers & variants, consumer/DPP
and media link/file objects, a full Nutrition group (43 per-nutrient
measurements), Food Serving & Details, Food Coding & Claims and packaging
controlled-code attributes — all sourced from the local Web Vocabulary snapshot.

### Nested objects

Selected **nested-object** properties are now authorable via a generic object
input type. The Builder renders an object's safe sub-fields and emits a typed
nested object, e.g.:

```json
"brand": { "@type": "gs1:Brand", "brandName": [ { "@language": "en", "@value": "…" } ] }
```

Supported object fields and their safe sub-fields:

- `gs1:brand` → `gs1:Brand` (brandName, subBrandName)
- `gs1:image` / `gs1:referencedFile` → `gs1:ReferencedFileDetails`
  (referencedFileURL, pixel size, file language)
- `gs1:certification` → `gs1:CertificationDetails` (standard, value, agency,
  identification, URI, start/end dates)
- `gs1:packagingMaterial` → `gs1:PackagingMaterial` (composition quantity,
  thickness)

Safe **scalar/langString/URL/quantity/date** sub-fields are offered directly.
Sub-fields whose range is a **controlled code list** are offered as a dropdown
and emitted as JSON-LD node references, e.g.:

```json
"hasAllergen": {
  "@type": "gs1:AllergenDetails",
  "allergenType": { "@id": "gs1:AllergenTypeCode-AM" },
  "allergenLevelOfContainmentCode": { "@id": "gs1:LevelOfContainmentCode-CONTAINS" }
}
```

- `gs1:hasAllergen` → `gs1:AllergenDetails` with `allergenType` (curated EU-14
  allergen codes from the local snapshot, with a "show full code list"
  checkbox to switch to all 385 WebVoc-defined `AllergenTypeCode` values —
  v0.23.0) and `allergenLevelOfContainmentCode` (Contains / Free from / May
  contain — already the full WebVoc-defined set, no toggle needed).

Sub-fields whose range is a nested *object* (e.g. an agency
`gs1:Organization`) are intentionally omitted. Objects with no sub-value entered
are not emitted.

Per-nutrient values (`…PerNutrientBasis`) are authored in the **Nutrition**
group as `value` + `unitCode` quantities on the food product, alongside the
nutrient basis quantity and an optional nutritional-claim statement. The older
`gs1:nutrientDetail` placeholder in the *Nutritional Information* group remains
`supported_in_v0_10: false` (it references a different structured concept).

This is a UI/config manifest plus the manual Builder serializer only — it is not
converter mapping YAML and does not change governed converter output. Manual
output stays prototype and is not BMS/XPath traceable.

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
