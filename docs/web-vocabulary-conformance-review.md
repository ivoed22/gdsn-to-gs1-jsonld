# Web Vocabulary Conformance Review

## Scope and evidence

This review summarizes the current mapping profile using:

- the v0.4.0 [mapping quality warning review](mapping-quality-warning-review-v0.4.0.md)
- `mapping_quality_report.json`
- `mapping_quality_report.xlsx`
- the Web Vocabulary-validated mapping catalog
- the catalog's GS1 Web Vocabulary term inventory
- the mapping review-issues CSV

The latest mapping quality report is valid in non-strict mode with 0 errors,
30 warnings, 32 informational findings, and 5 documented experimental
mappings. The warnings are governance and conformance-hardening work, not
evidence that the converter cannot produce usable JSON-LD.

## Strong / high-confidence areas

The following areas have strong traceability and validated GS1 Web Vocabulary
targets in the current local evidence:

| Area | Current assessment |
|---|---|
| GTIN | High-confidence BMS/XPath mapping to `gs1:gtin`; used in the GS1 Digital Link URI pattern |
| Product name | High-confidence mapping to `gs1:productName` with language support |
| Product description | High-confidence mapping to `gs1:productDescription` with language support |
| Brand | High-confidence mapping to `gs1:brandName` |
| GPC | High-confidence mapping to `gs1:gpcCategoryCode` |
| Net content | High-confidence mapping to `gs1:netContent` as a quantitative value |
| Ingredient statement | High-confidence mapping to `gs1:ingredientStatement` |
| Allergen structure and type | `gs1:hasAllergen`, `gs1:AllergenDetails`, and `gs1:allergenType` are validated; containment property needs replacement |
| Certification structure | `gs1:certification` and `gs1:CertificationDetails` are validated |
| Certification core fields | Standard, value, audit date, end date, and start-date candidate have validated terms, with some semantic selection still needed |

These fields support a credible demonstration of standards-traceable,
machine-readable product data. High confidence does not by itself make the
project catalog an official GS1 mapping publication.

## Needs review

### Nutrient modelling

The generic project properties `gs1:nutrientDetail`,
`gs1:nutrientTypeCode`, `gs1:quantityContained`, and
`gs1:preparationStateCode` were not found in the supplied Web Vocabulary
evidence. The catalog recommends reviewing specific nutrient properties,
`gs1:NutritionMeasurementType`, and `gs1:preparationCode`.

This is a modelling issue rather than an extraction problem. The source BMS
IDs and XPath expressions can be traceable while the target semantic model
still requires redesign.

### Product image modelling

`gs1:productImage` was not found in the supplied Web Vocabulary. The catalog
recommends considering `schema:image` or a GS1 link type / Digital Link
relation. The source selection also needs confirmation against the official
referenced-file mechanism and `PRODUCT_IMAGE` code filtering.

### Allergen containment

`gs1:levelOfContainment` was not found. The validated alternative is
`gs1:allergenLevelOfContainmentCode`. The allergen parent and type mappings are
otherwise strong.

### Certification semantics

The certification structure is strong, but several choices need clarification:

- use `gs1:certificationStartDate`, not the unvalidated
  `gs1:certificationEffectiveStartDate`
- determine whether `certificationIdentification` is best represented as a
  certification URI, certification value, or contextual identifier
- represent an issuing organization GLN without treating it automatically as
  an agency URL

### Generic referenced documents and DPP-like links

`gs1:referencedDocument` is a project extension, not a validated term in the
local Web Vocabulary evidence. `gs1:referencedFileTypeCode` was also not found
as a property. Schema.org document metadata is technically useful, but it is a
fallback outside GS1 Web Vocabulary.

The project needs a decision between embedded Schema.org document objects,
`gs1:certificationInfo`, GS1 Digital Link link relations, or another governed
document/DPP pattern.

### schema.org fallback usage

The project uses schema.org for URLs, document names, formats, identifiers, and
issuance dates where GS1 terms are absent or a semantic choice remains open.
This should be documented as mixed-vocabulary JSON-LD, not presented as proof
that every emitted property belongs to GS1 Web Vocabulary.

## Experimental mappings

Experimental mappings are useful for implementation and demonstration, but
should not be presented as final GS1 standards decisions.

Current experimental findings include:

- generic nutrient type and quantity properties
- the generic `gs1:referencedDocument` parent relationship
- document file-type representation through `schema:additionalType`
- selected certification identifier, issuer, and issuance-date alignments

Experimental status should remain visible in mapping catalogs, reports,
examples, and release documentation until an authoritative review resolves the
target model.

## Recommended terminology for claims

| Wording | Recommended use |
|---|---|
| **Web Vocabulary aligned** | Default description for current output: GS1 Web Vocabulary is the primary semantic target, with documented warnings and external fallbacks |
| **BMS/XPath traceable** | Mappings backed by catalogued GDSN BMS IDs and XPath evidence |
| **Web Vocabulary validated** | Individual properties or structures confirmed in the supplied Web Vocabulary sources |
| **Experimental** | Mappings not fully validated or requiring unresolved modelling/governance decisions |
| **Fully conformant** | Avoid until open warnings, vocabulary gaps, mixed-vocabulary policy, and mapping authority are resolved |

A mapping may be BMS/XPath traceable without its JSON-LD target being Web
Vocabulary validated. These are separate claims and should be reported
separately.

## Recommended next actions

1. Review and resolve the eight outstanding Web Vocabulary issues.
2. Decide the modelling pattern for generic and certification document links.
3. Clarify the DPP document relation strategy and relevant code-list usage.
4. Redesign or confirm nutrient modelling against current Web Vocabulary
   nutrition patterns.
5. Clarify certification issuer, scheme, identifier, and document modelling.
6. Separate official, candidate, needs-review, and experimental mappings in
   future documentation and catalogs.
7. Define a conformance wording policy and the evidence required for each
   claim.
8. Record the Web Vocabulary version or source revision used for validation.
