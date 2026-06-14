# v0.6.1 Warning Cleanup Review

## Summary

Version 0.6.1 reviewed all 15 warnings produced by `check-mapping` in v0.6.0.
Three warnings were tooling false positives: object parents were reported as
missing even though their child mappings were present in the catalog. They are
now informational findings. The 12 remaining warnings represent genuine
governance, Web Vocabulary, or modelling questions.

No converter output, mapping YAML, catalog row, or semantic mapping changed.

## Affected Files

- Web Vocabulary warnings originate from
  `mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv`.
- Structural parent findings compare `mapping/mapping_v0_3.yaml` with the
  catalog child rows.
- Certification identifier and issuance-date warnings compare
  `mapping/mapping_v0_3.yaml` with catalog property and coverage choices.
- Certification-document coverage warnings compare the catalog's
  `certification_documents[]` rows with the YAML `referenced_documents[]`
  model.
- The safe fix is confined to
  `src/gdsn_to_gs1_jsonld/catalog_quality.py`; no mapping source changed.

| Warning category | Count before | Count after | Fixed in v0.6.1? | Blocks release? | Notes |
| ---------------- | -----------: | ----------: | ---------------- | --------------- | ----- |
| `safe_fix_yaml_catalog_alignment` | 3 | 0 | Yes | No | Structural parents are covered by catalogued child mappings and are now reported as info. |
| `keep_governance_review` | 4 | 4 | No | No | Certification identifier, issuance date, and certification-document model require explicit decisions. |
| `keep_webvoc_term_review` | 2 | 2 | No | No | Allergen containment and certification start-date terms need reviewed replacements. |
| `keep_nutrient_modelling_review` | 3 | 3 | No | No | Generic nutrient properties are not validated in Web Vocabulary 1.17. |
| `keep_document_dpp_modelling_review` | 2 | 2 | No | No | File-type and document/DPP relationship modelling remain unresolved. |
| `keep_image_modelling_review` | 1 | 1 | No | No | The product-image target property or relation requires review. |
| **Total warnings** | **15** | **12** | **3 fixed** | **No** | Remaining warnings are explicit conformance and governance notes. |

## Detailed Review

| Warning | Category | Field/property | Action | Output changed? | Standards review required? |
| ------- | -------- | -------------- | ------ | --------------- | -------------------------- |
| Object parent absent as a separate catalog row | `safe_fix_yaml_catalog_alignment` | `allergens[]` | Report as structural coverage because catalogued allergen children exist. | No | No |
| Object parent absent as a separate catalog row | `safe_fix_yaml_catalog_alignment` | `nutrients[]` | Report as structural coverage because catalogued nutrient children exist. | No | No |
| Object parent absent as a separate catalog row | `safe_fix_yaml_catalog_alignment` | `referenced_documents[]` | Report as structural coverage because catalogued document children exist; keep the experimental parent-property info. | No | No |
| YAML property differs from catalog choices | `keep_governance_review` | `certifications[].certification_identification` | Keep `schema:identifier` experimental until URI/value semantics are decided. | No | Yes |
| YAML field has no catalog row | `keep_governance_review` | `certifications[].certificate_issuance_date_time` | Keep documented `schema:dateIssued` fallback pending catalog governance. | No | Yes |
| High-confidence catalog field not represented under the same object | `keep_governance_review` | `certification_documents[].file_name` | Decide whether certification documents are aliases, subsets, or separate from generic referenced documents. | No | Yes |
| High-confidence catalog field not represented under the same object | `keep_governance_review` | `certification_documents[].document_url` | Decide the certification-document relationship and use of the stable `certificationInfo` linktype. | No | Yes |
| Web Vocabulary property not found | `keep_image_modelling_review` | `product_image_url` / `gs1:productImage` | Review `schema:image` or a governed GS1 link relation. | No | Yes |
| Current property not found; replacement exists | `keep_webvoc_term_review` | `allergens[].level_of_containment` | Review `gs1:allergenLevelOfContainmentCode`. | No | Yes |
| Generic nutrient model not found | `keep_nutrient_modelling_review` | `nutrients[].preparation_state` | Review `gs1:preparationCode` in the target nutrient model. | No | Yes |
| Generic nutrient model not found | `keep_nutrient_modelling_review` | `nutrients[].nutrient_type` | Redesign against validated specific nutrient properties and `gs1:NutritionMeasurementType`. | No | Yes |
| Generic nutrient model not found | `keep_nutrient_modelling_review` | `nutrients[].quantity_contained` | Redesign quantity modelling together with the nutrient target model. | No | Yes |
| One catalog choice is not found | `keep_webvoc_term_review` | `certifications[].effective_start` | Confirm `gs1:certificationStartDate` as the governed target. | No | Yes |
| File-type property not found | `keep_document_dpp_modelling_review` | `certification_documents[].referenced_file_type` | Decide whether to use `schema:additionalType`, a code value, or another governed pattern. | No | Yes |
| File-type property not found | `keep_document_dpp_modelling_review` | `referenced_documents[].referenced_file_type` | Resolve file-type representation together with the generic DPP/document model. | No | Yes |

## Reporting Changes

Every quality message now includes:

- `severity`
- `category`
- `affected_field_property`
- `reason`
- `recommended_action`
- `blocks_release`
- `standards_review_required`

Web Vocabulary warnings now include the catalog validation evidence in their
reason. Category-specific actions distinguish nutrient, image, document/DPP,
and replacement-term review.

## Recommendation

The remaining 12 warnings should feed a v0.7.0 standards-review track rather
than an automatic code cleanup. Priority decisions are nutrient modelling,
document/DPP relationships, image representation, allergen containment, and
certification semantics. Stronger conformance claims should wait for those
decisions, but the warnings do not block v0.6.1.
