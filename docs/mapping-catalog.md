# Mapping catalog

Technical YAML mappings under `mapping/` are executable converter
configuration. Files under `mapping_catalog/` are the standards traceability
and governance layer.

The catalog connects GDSN 3.1.36 BMS IDs and official XPath expressions to:

- canonical model fields
- JSON-LD properties
- mapping status and confidence
- GS1 Web Vocabulary validation status
- review notes and recommended actions

Version 0.3.0 is the first release designed from this catalog. The catalog was
prepared using local GS1 Web Vocabulary JSON-LD and Turtle sources; the
converter does not fetch or dereference those sources.

## Governance decisions

Certification has comparatively strong vocabulary support:

- `gs1:certification`
- `gs1:CertificationDetails`
- `gs1:certificationStandard`
- `gs1:certificationValue`
- `gs1:certificationAuditDate`
- `gs1:certificationStartDate`
- `gs1:certificationEndDate`

Schema.org terms are used for document metadata. The generic document parent
relationship `gs1:referencedDocument` is an explicit experimental extension
because it is not present in the validated vocabulary. File type codes use the
catalog-recommended `schema:additionalType` rather than claiming
`gs1:referencedFileTypeCode` is official.

Review-risk mappings remain experimental until standards review resolves them.
