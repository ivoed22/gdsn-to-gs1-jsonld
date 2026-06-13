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

## Quality checks

Version 0.4.0 treats the CSV as machine-readable governance input. The
`check-catalog` command validates the canonical required column set, mapped and
candidate row completeness, BMS identifiers, mapping status, confidence, and
Web Vocabulary review metadata.

The canonical column set includes:

- GDSN identity and structure: `gdsn_bms_id`, `gdsn_attribute_name`,
  `gdsn_xpath`, `gdsn_module`, `gdsn_datatype`, `gdsn_cardinality`, `code_list`
- mapping targets: `canonical_field`, `jsonld_property`, `jsonld_structure`,
  `jsonld_object_type`, `technical_mapping_file`
- governance: `mapping_version`, `scope_group`, `mapping_status`, `confidence`,
  `notes`, `source`, `review_action`
- vocabulary review: `webvoc_property_status`,
  `webvoc_property_validation`, `recommended_jsonld_property`

The current catalog also contains useful additional Web Vocabulary label,
range, and object-type columns. They remain supported but are not mandatory.
Unknown statuses are warnings by default so catalog vocabulary can evolve
without hiding the finding or breaking non-strict checks.

See [`mapping-quality-checks.md`](mapping-quality-checks.md) for CLI behavior
and report contents.
