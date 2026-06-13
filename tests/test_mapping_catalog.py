import csv
from pathlib import Path


REQUIRED_COLUMNS = {
    "mapping_version",
    "scope_group",
    "gdsn_bms_id",
    "gdsn_attribute_name",
    "gdsn_xpath",
    "canonical_field",
    "jsonld_property",
    "mapping_status",
    "confidence",
    "webvoc_property_status",
    "recommended_jsonld_property",
    "review_action",
}


def test_mapping_catalog_csv_exists_and_has_required_columns():
    path = Path(
        "mapping_catalog/"
        "gdsn_to_gs1_web_vocabulary_mapping_catalog_v0_3_webvoc_validated.csv"
    )
    assert path.is_file()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert REQUIRED_COLUMNS <= set(reader.fieldnames or [])
        rows = list(reader)
    assert any(row["mapping_version"] == "v0.3.0 candidate" for row in rows)
