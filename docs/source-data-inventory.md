# Public Source Data Inventory

Version v0.9.1 introduces a small, explicit inventory for public standards
source data used by the converter evidence layer.

This inventory is preparatory. It supports future review and prototyping work
without changing converter logic, mapping YAML, catalog data, or Web Vocabulary
snapshots.

## Sources

| Source | Version | Public URL | Local path | SHA-256 |
| --- | --- | --- | --- | --- |
| GDSN Attributes with BMSId and XPath | 3.1.36 | <https://www.gs1.org/docs/gdsn/3.1/GDSN_Attributes_with_BMSId_xPath_3.1.36_June_5_2026.xlsx> | `reference_data/raw_public/GDSN_Attributes_with_BMSId_xPath_3.1.36_June_5_2026.xlsx` | `1912edf47ea73295b57979b0cc1ae868f3955c1b16684ced08a85eff7f19be75` |
| GS1 Web Vocabulary JSON-LD | 1.17 | <https://ref.gs1.org/voc/data/gs1Voc.jsonld> | `webvoc/current/gs1Voc.jsonld` | `cf48c79d5891195a30f873b333983b21ffacb518adc80568cf1141961a3889b9` |

The GDSN workbook is committed under `reference_data/raw_public/` as a public
source copy for repeatable offline import. The Web Vocabulary JSON-LD file is
not duplicated there because the repository already carries the current local
snapshot under `webvoc/current/`.

## Manifest

The source manifest is:

```text
reference_data/source_manifest.json
```

It records:

- source ID and title
- public source URL
- retrieval timestamp
- source version
- local path
- SHA-256 checksum
- public accessibility flag
- authority/derivation note
- intended project usage
- rights and usage notes

The lightweight schema reference is:

```text
reference_data/schemas/source_manifest.schema.json
```

## Normalized Outputs

The v0.9.1 import writes normalized files under:

```text
reference_data/normalized/
```

Committed normalized outputs:

- `gdsn_attributes_bms_xpath_3_1_36.csv`
- `gdsn_attributes_bms_xpath_3_1_36.json`
- `webvoc_properties_1_17.csv`
- `webvoc_properties_1_17.json`
- `webvoc_classes_1_17.csv`
- `webvoc_classes_1_17.json`
- `source_data_summary.json`

## Inventory Counts

The committed `source_data_summary.json` reports:

- GDSN workbook sheets: 3
- selected GDSN sheet: `3.1.36`
- active GDSN rows: 7110
- total GDSN rows including deleted attributes: 7171
- GDSN attribute rows: 6067
- GDSN class rows: 990
- deleted GDSN rows: 61
- candidate source rows: 6007
- Web Vocabulary classes: 55
- Web Vocabulary properties: 553
- Web Vocabulary link-type properties: 60

Inventory findings are retained rather than suppressed:

- duplicate BMS IDs: none reported
- duplicate XPath values: 9 possible duplicate values reported
- missing GDSN `row_type`: 1 row reported
- missing Web Vocabulary labels/comments/domains/ranges: none reported

## Scope Boundaries

This inventory does not:

- generate mapping YAML
- change the converter output
- change batch conversion behavior
- change catalog data
- change the existing Web Vocabulary snapshot
- suppress warnings

Future v0.10.0 and v0.11.0 work may use these normalized references, but those
features are intentionally not implemented in v0.9.1.
