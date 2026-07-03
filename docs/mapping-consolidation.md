# Mapping profile consolidation (v0.15.0)

## Why

Before full-scope mapping scoring, hard-mapping review, codelist enforcement,
or DPP crosswalk work, the mapping foundation must be unambiguous. Until
v0.14.0 the repository carried four mapping-related artifacts with
overlapping content:

| Artifact | Role | State after v0.15.0 |
|---|---|---|
| `mapping/mapping_registry.yaml` | **Current** — consolidated executable profile + governance | new, authoritative |
| `mapping/mapping_v0_3.yaml` | previous default executable profile (28 attributes) | archived, reference only |
| `mapping/mapping_v0_2.yaml` | food-information profile (16 attributes) | archived, reference only |
| `mapping/mapping_mvp.yaml` | MVP profile (9 attributes) | archived, reference only |
| `mapping_catalog/*.csv` | governance review catalog (29 rows) | unchanged, source of the registry's catalog section |

Users should not need to understand old profile history to start converting:
the app now defaults to the registry, and old profiles appear only inside an
"Archived mapping profiles" expander with an explicit warning when selected.

## The registry format

`mapping/mapping_registry.yaml` is a superset of the executable mapping
schema:

```yaml
metadata:            # provenance, registry_version, status vocabulary
settings:            # identical to mapping_v0_3.yaml
fields:              # executable, identical to v0_3 + per-field governance
object_mappings:     # executable, identical to v0_3 + governance
catalog:             # full review catalog (converter never reads this)
```

Key properties:

- The converter's loader (`mapping_loader.py`, pydantic) ignores unknown
  keys, so the registry is executed exactly like `mapping_v0_3.yaml` with
  **zero loader changes**. Equivalence is enforced by
  `tests/test_mapping_registry.py` (byte-identical conversion output).
- Registry `status` uses a fixed vocabulary: `proposed`, `review_required`,
  `accepted`, `rejected`, `deprecated`, `blocked`. There is deliberately no
  `hard_mapping_candidate` status — hard-mapping (Track B, v0.16.0) is a
  flag plus a dedicated review lane, never a terminal status.
- Original catalog `mapping_status` values (`mapped_official_bms_xpath`,
  `candidate_*`, `needs_*_review`) are preserved verbatim as
  `catalog_status`. Normalization rule: every currently implemented row is
  `accepted`; any row whose catalog status is not
  `mapped_official_bms_xpath` additionally carries `review_required: true`
  (17 of 29 rows).
- Catalog rows and executable YAML fields are not 1:1. The generation script
  (`scripts/build_mapping_registry.py`) carries an explicit alias table:
  `net_content` governs both `net_content_value` and `net_content_unit`;
  `certification_documents[]`/`referenced_documents[]` catalog groups both
  map onto the single `referenced_documents` object mapping;
  `nutrients[].quantity_contained` governs the value and unit fields.
  YAML fields without any catalog row (e.g.
  `certifications[].certificate_issuance_date_time`, an experimental
  schema.org alignment) are conservatively flagged `review_required: true`.

## Regeneration

The registry is generated — do not edit it by hand. Changing accepted
mappings remains a reviewed standards decision, exactly as it was for the
mapping YAML before consolidation:

```bash
python scripts/build_mapping_registry.py
```

Regeneration is deterministic and idempotent (enforced by test). The source
files (`mapping_v0_3.yaml` and the catalog CSV) are never modified.

## Programmatic access

`src/gdsn_to_gs1_jsonld/mapping_registry.py`:

- `load_registry()` — full registry with structural and status validation.
- `registry_catalog_rows()` — review rows shaped like the catalog CSV rows.
- `registry_field_governance()` — governance block per executable field
  (`canonical_field` or `object[].field` keys).
- `registry_summary()` — deterministic counts by status and review flag.

The converter keeps using `mapping_loader.load_mapping()`; review tooling
uses this module. Track B (v0.16.0) extends the catalog section with scored,
non-implemented candidate rows using the other vocabulary statuses.

## Governance

- Accepted registry statuses are project review decisions, not official GS1
  decisions.
- No official GS1 validation, EU DPP compliance, or production readiness is
  claimed.
- The registry and everything generated from it must never contain DPP
  Keystone (dppk) terms or namespaces (`tests/test_no_dppk.py`).
