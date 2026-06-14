# v0.4.0 Mapping Quality Warning Review

## Scope

This review summarizes the mapping quality findings generated for
`mapping/mapping_v0_3.yaml` against
`mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv`.

The `check-mapping` report contains 30 warnings. The 23 warnings produced by
`check-catalog` are a subset of those 30 and are not added again. The report is
valid in non-strict mode and contains no errors.

The categories below are a primary classification: each warning is counted
once, so the warning counts total exactly 30. Cross-cutting document and Web
Vocabulary concerns are explained in the detailed sections.

## Summary

| Category | Warning count | Affected fields/properties | Severity | Blocks release? | Recommended action |
|---|---:|---|---|---|---|
| Web Vocabulary term not found / not validated | 8 | `product_image_url`; allergen containment; nutrient preparation, type, and quantity; certification start date; certification and generic document file types | High standards-review priority | No | Select validated replacement terms where available; redesign nutrient and file-type modelling where no direct term exists. |
| Experimental mapping | 0 warnings; 5 info findings | `gs1:nutrientTypeCode`; `gs1:quantityContained`; `gs1:referencedDocument`; document `schema:additionalType` | Medium | No | Keep explicitly marked experimental; obtain standards decisions before promoting these mappings to stable/official status. |
| Missing or uncertain BMS ID | 0 | No automated missing-BMS warning. `product_page_url` remains a separate BMS review item despite catalog BMS ID `3000`. | Low | No | Confirm the official product-page/e-content mechanism and XPath during the next BMS review. |
| YAML mapping not fully supported by catalog | 5 | `allergens[]`; `nutrients[]`; `certifications[].certificate_issuance_date_time`; `referenced_documents[]`; `certifications[].certification_identification` / `schema:identifier` | Medium | No | Add or align catalog parent/object rows and document the issuance-date and identifier decisions. |
| Catalog mapping not implemented in YAML | 2 | `certification_documents[].file_name`; `certification_documents[].document_url` | Medium | No | Reconcile the catalog's certification-document object with the YAML's filtered `referenced_documents[]` model; implement or mark intentionally not implemented. |
| DPP/document-link modelling issue | 7 | All catalog rows under `certification_documents[]` and `referenced_documents[]` have an unrecognized candidate status | High standards-review priority | No | Decide the document parent relation, object type, file-type property, and DPP/certification code-list treatment; then normalize statuses. |
| Other | 8 | `product_image_url` and seven certification fields with unrecognized governance statuses | Medium | No | Add the intended status vocabulary to the checker or migrate catalog rows to the canonical status set after semantic review. |
| **Total warning records** | **30** |  |  | **No** | Resolve high-priority standards questions before claiming full GS1 Web Vocabulary alignment. |

## Web Vocabulary Review

Eight warning records require vocabulary review:

1. `product_image_url`: `gs1:productImage` was not found. The catalog recommends
   considering `schema:image` or a GS1 link type / Digital Link relation.
2. `allergens[].level_of_containment`: `gs1:levelOfContainment` was not found.
   The catalog identifies `gs1:allergenLevelOfContainmentCode` as the available
   replacement.
3. `nutrients[].preparation_state`: neither the generic
   `gs1:nutrientDetail` model nor `gs1:preparationStateCode` was found. The
   catalog recommends reviewing `gs1:preparationCode`.
4. `nutrients[].nutrient_type`: `gs1:nutrientDetail` and
   `gs1:nutrientTypeCode` were not found. This needs a nutrient-model decision
   using specific GS1 nutrient properties and `gs1:NutritionMeasurementType`.
5. `nutrients[].quantity_contained`: `gs1:nutrientDetail` and
   `gs1:quantityContained` were not found. This shares the nutrient-model
   decision above.
6. `certifications[].effective_start`: `gs1:certificationStartDate` exists,
   while `gs1:certificationEffectiveStartDate` was not found. Select the
   validated `gs1:certificationStartDate`.
7. `certification_documents[].referenced_file_type`:
   `gs1:referencedFileTypeCode` was not found as a property.
8. `referenced_documents[].referenced_file_type` has the same missing-property
   issue. Code values may exist, but that does not establish the property.

These findings do not invalidate the v0.4.0 quality-check release. They do
block treating the affected mappings as fully validated GS1 Web Vocabulary
alignments.

## Experimental Findings

Experimental mappings are reported as five informational findings, not warning
records:

- `nutrients[].nutrient_type_code` using `gs1:nutrientTypeCode`
- `nutrients[].quantity_contained.value` using
  `gs1:quantityContained.value`
- `nutrients[].quantity_contained.unit_code` using
  `gs1:quantityContained.unitCode`
- `referenced_documents[]` using the project extension
  `gs1:referencedDocument`
- `referenced_documents[].referenced_file_type` using
  `schema:additionalType`

The nutrition findings require a model review. The document findings require a
decision on whether Schema.org `DigitalDocument` modelling, a GS1 certification
link, a Digital Link relation, or another external vocabulary should carry the
relationship.

## BMS Review

No warning reports a missing BMS ID. Official/high-confidence catalog rows have
BMS identifiers where required by the current checker.

One non-warning review item remains: `product_page_url` uses BMS ID `3000`, but
the catalog notes that the correct official product-page, e-content, or
referenced-file mechanism still needs confirmation. This is a provenance and
XPath review, not a v0.4.0 release blocker.

## YAML and Catalog Alignment

Five warnings show YAML mappings that are not fully represented by the catalog:

- object parent `allergens[]`
- object parent `nutrients[]`
- `certifications[].certificate_issuance_date_time` /
  `schema:dateIssued`
- object parent `referenced_documents[]` /
  experimental `gs1:referencedDocument`
- `certifications[].certification_identification`, where YAML uses
  `schema:identifier` but the catalog lists `gs1:certificationURI` or
  `gs1:certificationValue`

Two warnings show high-confidence catalog fields not implemented under the same
canonical object in YAML:

- `certification_documents[].file_name`
- `certification_documents[].document_url`

The likely reconciliation point is the distinction between the catalog's
`certification_documents[]` object and the YAML's filtered
`referenced_documents[]` object. Standards review should decide whether these
are separate models, aliases, or one shared document model with typed
relationships.

## DPP and Document Links

Seven warning records are assigned to this category because all three
`certification_documents[]` rows and all four `referenced_documents[]` rows use
the catalog status `candidate_official_bms_xpath`, which is not in the current
canonical allowed-status set.

These status warnings are governance warnings rather than evidence that the
official GDSN XPath is wrong. The underlying standards questions are:

- Is there a valid generic parent relationship for a referenced document?
- Should certification documents use `gs1:certificationInfo`, a Schema.org
  `DigitalDocument`, or both?
- Which property carries `ReferencedFileTypeCode` when
  `gs1:referencedFileTypeCode` is not defined?
- Are `DPP_DOCUMENT` and `CERTIFICATION_DOCUMENT` valid values in the relevant
  code list?
- Should the certification-document and generic referenced-document catalog
  objects remain distinct?

Until these questions are resolved, the document mappings should remain
explicitly experimental or candidate mappings.

## Other Governance Warnings

Eight warnings concern unrecognized status values outside the document groups:

- `product_image_url`: `candidate_needs_code_filter_review`
- `certifications[].certification_standard`:
  `candidate_official_bms_xpath`
- `certifications[].certification_identification`:
  `needs_semantic_review`
- `certifications[].certification_value`:
  `candidate_official_bms_xpath`
- `certifications[].certification_organisation_identifier`:
  `needs_semantic_review`
- `certifications[].assessment_date`: `candidate_official_bms_xpath`
- `certifications[].effective_end`: `candidate_official_bms_xpath`
- `certifications[].effective_start`: `needs_web_vocab_review`

The catalog and checker should converge on one controlled status vocabulary.
Before normalization, preserve the distinctions represented by code-filter,
semantic, BMS, and Web Vocabulary review states rather than replacing them with
a less specific status.

Two certification semantic decisions deserve explicit review:

- `certificationIdentification` may represent a value or URI depending on the
  source value.
- `certificationOrganisationIdentifier` is a GLN for the issuing organization,
  not automatically an agency URL.

## Release Assessment

No warning should retroactively block the v0.4.0 release. The release provides
quality-check tooling, reports all findings, exits successfully with no errors,
and does not claim that every mapped term is standards-final.

The high-priority items should block stronger claims of standards conformance
for the affected fields until the Web Vocabulary, nutrient model, and generic
document-link decisions are resolved.

## Reports Inspected

- `mapping_quality_report/mapping_quality_report.json`
- `mapping_quality_report/mapping_quality_report.xlsx`
- `check-catalog` output: 23 warnings, all included in the 30-warning mapping
  report
- `check-mapping` output: 30 warnings and 32 informational findings
- mapping catalog rows used to interpret BMS IDs, recommended properties,
  review actions, and vocabulary validation details
