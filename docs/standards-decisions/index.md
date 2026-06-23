# Standards Decision Register

Version 0.7.1 links the six open standards decisions to GitHub Issues so each
topic can be discussed and tracked outside the Markdown records. These records
document choices; they do not change converter output or claim that unresolved
mappings are conformant.

## Nutrient modelling

| ID | Title | Current mapping status | Affected fields/properties | Warning category | Recommended owner/reviewer | Status | Target release | Record | Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SDR-001 | Nutrient modelling | Experimental, Web Vocabulary review required | `nutrients[].preparation_state`, `nutrient_type`, `quantity_contained`; `gs1:nutrientDetail`, `gs1:nutrientTypeCode`, `gs1:quantityContained` | `nutrient_modelling` | GS1 Web Vocabulary owner and sector experts | Open | v0.8.0 or standards-approved mapping release | [SDR-001](SDR-001-nutrient-modelling.md) | [#4](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/4) |

## Document and DPP modelling

| ID | Title | Current mapping status | Affected fields/properties | Warning category | Recommended owner/reviewer | Status | Target release | Record | Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SDR-002 | Document and DPP modelling | Experimental document object and file-type fallback | Document file types; `gs1:referencedFileTypeCode`, `schema:additionalType`, `gs1:dpp`, `gs1:certificationInfo` | `document_dpp_modelling` | GS1 Architecture and DPP/data spaces workstream | Open | v0.8.0 or deferred | [SDR-002](SDR-002-document-dpp-modelling.md) | [#2](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/2) |

## Image representation

| ID | Title | Current mapping status | Affected fields/properties | Warning category | Recommended owner/reviewer | Status | Target release | Record | Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SDR-003 | Image representation | Candidate requiring Web Vocabulary review | `product_image_url`; `gs1:productImage`, `schema:image` | `image_modelling` | GS1 Web Vocabulary owner | Open | v0.8.0 | [SDR-003](SDR-003-image-representation.md) | [#5](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/5) |

## Allergen containment

| ID | Title | Current mapping status | Affected fields/properties | Warning category | Recommended owner/reviewer | Status | Target release | Record | Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SDR-004 | Allergen containment | BMS/XPath mapped; target term needs replacement review | `allergens[].level_of_containment`; `gs1:levelOfContainment`, `gs1:allergenLevelOfContainmentCode` | `webvoc_term_missing` | GS1 Web Vocabulary owner and food sector experts | Open | v0.8.0 | [SDR-004](SDR-004-allergen-containment.md) | [#7](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/7) |

## Certification semantics

| ID | Title | Current mapping status | Affected fields/properties | Warning category | Recommended owner/reviewer | Status | Target release | Record | Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SDR-005 | Certification semantics | Mixed validated, fallback, and semantic-review targets | Certification identification, issuance date, effective start | `certification_semantics` | GS1 Web Vocabulary owner and GDSN/GSMP group | Open | v0.8.0 | [SDR-005](SDR-005-certification-semantics.md) | [#8](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/8) |

## YAML/catalog governance

| ID | Title | Current mapping status | Affected fields/properties | Warning category | Recommended owner/reviewer | Status | Target release | Record | Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SDR-006 | YAML and catalog governance | Catalog and YAML use different certification-document object boundaries | `certification_documents[].file_name`, `document_url`; generic `referenced_documents[]` | `yaml_catalog_mismatch` | Internal project owner and mapping governance group | Open | v0.8.0 or governance decision | [SDR-006](SDR-006-yaml-catalog-governance.md) | [#9](https://github.com/ivoed22/gdsn-to-gs1-jsonld/issues/9) |

## Machine-readable backlog

- [JSON backlog](standards_review_backlog.json)
- [CSV backlog](standards_review_backlog.csv)

Refresh these files with:

```bash
gdsn-to-gs1-jsonld export-standards-backlog \
  --warning-review docs/warning-cleanup-v0.6.1.md \
  --output docs/standards-decisions/ \
  --format all
```

The structured backlog is maintained in the package rather than parsed from
Markdown. Detailed SDR files remain human-maintained and are never overwritten
by the export command.
