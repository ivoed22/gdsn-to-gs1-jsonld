"""Build the review-safe v0.4 mapping profile from archived v0.3.

The profile deliberately removes mappings whose GS1 properties are absent
from the committed Web Vocabulary snapshot. Candidate expansion remains
review-only until BMS IDs and official XPaths have been confirmed.
"""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mapping" / "mapping_v0_3.yaml"
TARGET = ROOT / "mapping" / "mapping_v0_4.yaml"


def build() -> dict:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    data["metadata"] = {
        "name": "GDSN to GS1 JSON-LD Review-safe WebVoc Profile",
        "version": "0.4.0",
        "description": (
            "Versioned review-safe successor to v0.3. Emits only GS1 terms "
            "verified in the committed Web Vocabulary snapshot. Unsupported "
            "or lossy source values remain in the unmapped source evidence report."
        ),
        "derived_from": "mapping/mapping_v0_3.yaml",
        "webvoc_snapshot": "webvoc/current/gs1Voc.jsonld",
    }

    object_mappings = {
        item["id"]: item for item in data.get("object_mappings", [])
    }

    allergens = object_mappings["allergens"]
    for field in allergens["fields"]:
        if field["id"] == "level_of_containment":
            field["jsonld_property"] = "gs1:allergenLevelOfContainmentCode"

    # v0.3 used generic GS1 nutrient terms that are not present in the
    # committed vocabulary. Preserve these values only in unmapped evidence.
    object_mappings.pop("nutrients", None)

    referenced = object_mappings["referenced_documents"]
    referenced["description"] = "Official referenced-file details"
    referenced["jsonld_property"] = "gs1:referencedFile"
    referenced["object_type"] = "gs1:ReferencedFileDetails"
    for field in referenced["fields"]:
        if field["id"] == "document_file_type":
            field["jsonld_property"] = "gs1:referencedFileTypeCode"

    data["object_mappings"] = list(object_mappings.values())
    data["candidate_expansion"] = {
        "status": "review_required",
        "source": "mapping_catalog/gdsn_to_gs1_web_vocabulary_mapping_candidates_v0_4.csv",
        "policy": (
            "Candidates are not executable until BMS ID, official XPath, "
            "cardinality, WebVoc domain/range, and codelist semantics are reviewed."
        ),
    }
    return data


if __name__ == "__main__":
    TARGET.write_text(
        yaml.safe_dump(build(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(TARGET)
