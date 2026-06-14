# Web Vocabulary Update Monitor

## Why monitoring is needed

GS1 Web Vocabulary and GS1 Digital Link link types evolve independently from
the converter. A mapping catalog can therefore be accurate against one
snapshot and require review against a later official publication.

Version 0.6.0 adds controlled monitoring so changes are visible without
silently rewriting semantic mappings. Normal XML conversion remains fully
offline and never fetches external vocabulary resources.

## Local snapshot structure

The repository snapshot is stored under `webvoc/current/`:

- `gs1Voc.jsonld`
- `gs1Voc.ttl`
- `linktypes.json`
- `metadata.json`

Metadata records source URLs, fetch time, SHA256 hashes, detected vocabulary
version, and detected last-modified value.

## Check for updates

Compare official resources with the local snapshot:

```bash
gdsn-to-gs1-jsonld check-webvoc-updates \
  --snapshot-dir webvoc/current \
  --output webvoc_update_report/
```

Run an offline validation using only committed snapshots:

```bash
gdsn-to-gs1-jsonld check-webvoc-updates \
  --snapshot-dir webvoc/current \
  --output webvoc_update_report/ \
  --no-network
```

The command writes JSON and Excel reports with hashes, change flags, term
counts, detectable term and linktype differences, warnings, and recommended
actions.

To replace snapshots after reviewing detected changes, rerun with
`--update-snapshot`. Snapshot replacement is explicit and cannot be combined
with `--no-network`.

## Revalidate the mapping catalog

```bash
gdsn-to-gs1-jsonld revalidate-mapping-catalog \
  --catalog mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv \
  --webvoc-dir webvoc/current \
  --output mapping_catalog_revalidation/
```

The source catalog is not overwritten. Add `--write-updated-catalog` to write
`mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_6_revalidated.csv`.
Only Web Vocabulary validation/status columns are updated. Canonical fields,
BMS IDs, XPath values, and JSON-LD properties are preserved.

## Safe automatic updates

The tools may safely:

- download and hash official snapshots;
- compare term and linktype inventories;
- record version and last-modified metadata;
- update derived validation status, labels, ranges, and evidence;
- recognize stable linktypes such as `dpp` and `certificationInfo`;
- produce review reports and a new catalog copy.

## Standards review required

The tools do not automatically:

- replace a JSON-LD property;
- change a canonical field, BMS ID, XPath, or mapping YAML;
- decide nutrient, image, certification, document, or DPP modelling;
- promote an experimental mapping to an official mapping;
- claim complete GS1 Web Vocabulary conformance.

Warnings remain when they represent genuine modelling or governance choices.
Each quality warning includes a category, affected field/property, reason,
recommended action, severity, and release-blocking flag.
