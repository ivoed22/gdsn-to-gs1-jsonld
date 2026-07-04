# GDSN Codelist Registry & Validation (Track D, v0.20.0)

## Source

`reference_data/raw_public/GDSN_and_Shared_Code_Lists_r3p1p36_i6_8May2026.xlsx`
— the official public GDSN and Shared Common Code Lists export for release
3.1.36. Provided directly by the user (not fetched by this project); see
its entry in `reference_data/source_manifest.json`
(`gdsn_and_shared_code_lists_r3p1p36_i6`) for the license/rights note and
checksum. Because the exact public GS1 download URL was not independently
confirmed, `source_url` is a project-internal URN, not a guessed link.

This unblocks the codelist enforcement work that was deferred since
v0.15.0/v0.16.0: the reference data already had 507 codelist *names*
(`code_list_name` on GDSN attributes) but zero value enumerations. This
workbook has the actual values: 595 codelists, 14,564 values, 509
deprecated ("Deleted Codes") values with sunset release.

## Import

```bash
gdsn-to-gs1-jsonld import-codelists \
  --codelist-xlsx reference_data/raw_public/GDSN_and_Shared_Code_Lists_r3p1p36_i6_8May2026.xlsx \
  --output-dir reference_data/normalized/
```

Writes `reference_data/normalized/gdsn_codelists_r3_1_36.json` (the
registry, committed) and `..._summary.json`. Deterministic: codelists and
their values are sorted; re-running produces identical output for the same
source file.

Registry shape:

```json
{
  "source_version": "3.1.36",
  "source_local_path": "...",
  "source_sha256": "...",
  "codelists": {
    "AllergenTypeCode": {
      "semantic_resource_urn": "urn:gs1:gdd:cl:AllergenTypeCode",
      "domain": "GDSN",
      "status": "CURRENT",
      "values": [{"value": "AM", "label": "...", "definition": "...", "status": "CURRENT"}, ...],
      "deprecated_values": [{"value": "...", "label": "...", "definition": "...", "sunset_release": "3.1.19"}, ...]
    }
  }
}
```

## Validation

`src/gdsn_to_gs1_jsonld/codelist_registry.py`:

- `validate_code_value(registry, codelist_name, value) -> (status, detail)`
  — status is one of `valid` / `unknown` / `deprecated` / `missing` /
  `source_unavailable`. Case-insensitive, trimmed comparison (matching how
  the converter already uppercases code values).
- `CODELIST_DEPENDENCIES` — a **curated, verified static table** mapping
  `CanonicalProduct` field names to codelist names:

  | Canonical field | Codelist |
  |---|---|
  | `net_content_unit` | `MeasurementUnitCode_GDSN` |
  | `allergens[].allergen_type` | `AllergenTypeCode` |
  | `allergens[].level_of_containment` | `LevelOfContainmentCode` |
  | `nutrients[].nutrient_type_code` | `NutrientTypeCode` |
  | `nutrients[].preparation_state_code` | `PreparationTypeCode` |
  | `referenced_documents[].referenced_file_type` | `ReferencedFileTypeCode` |

  This is deliberately **not** derived from the mapping registry catalog's
  `code_list` column: that governed data predates several YAML field
  renames (e.g. the catalog says `nutrients[].preparation_state`, but
  `CanonicalProduct` has `preparation_state_code`) and one row
  (`product_image_url`) carries a `code_list` value that isn't semantically
  a code field at all. Rather than trust those inconsistencies for a
  runtime-enforcement feature, every entry above was independently verified
  against both the real field name and the imported registry's actual
  codelist name.

- `validate_canonical_product_codelists(product_dump, dependencies, registry)`
  — runs every dependency against a serialized `CanonicalProduct`
  (`product.model_dump()`), including one level of object-mapping nesting.

## Converter integration — fully opt-in, never blocking by itself

`convert_xml_to_jsonld(..., codelist_registry=None)`: a new, optional,
keyword-only parameter.

- **Not passed (default)**: behavior is byte-identical to every version
  before v0.20.0. `ConversionResult.codelist_validation` is an empty list;
  nothing else changes. Every existing caller is unaffected.
- **Passed a loaded registry**: `ConversionResult.codelist_validation` is
  populated with one entry per codelist-backed field
  (`canonical_field`, `code_list`, `value`, `status`, `detail`).
  `jsonld_data`, `mapping_report_rows`, `validation_report`, and
  `unmapped_fields` are identical either way — codelist validation is
  strictly additive diagnostic information.

Whether a non-`valid` status should warn or block conversion is entirely
the caller's decision — `convert_xml_to_jsonld` itself never raises or
changes output based on codelist validation results. On the committed
example fixture, two `referenced_file_type` values
(`DPP_DOCUMENT`, `CERTIFICATION_DOCUMENT`) come back `unknown`: they are
project-defined sentinel values for the already-documented experimental
`referencedDocument` mapping (see `docs/v0.3.0-design.md`), not real GS1
`ReferencedFileTypeCode` values — a genuine, expected finding, not a bug.

## UI (v0.21.0)

The Convert GDSN XML workflow shows codelist validation in an "Open
codelist validation (Track D)" expander inside Step 2 (Review mapping &
evidence): status counts, a table, and a per-entry detail view with a
status badge. See `docs/streamlit-app.md`. It never adds a 5th download —
codelist validation stays diagnostic, not part of the exported files.

## What this does NOT do

- Does NOT change `jsonld_data` output, ever.
- Does NOT block conversion by default, or at all unless a caller builds
  that behavior on top of `codelist_validation`.
- Does NOT claim official GS1 validation or production compliance.
- Does NOT enforce codelists for fields outside `CODELIST_DEPENDENCIES`.
- Does NOT add codelist validation results to any of the four existing
  downloadable reports.
