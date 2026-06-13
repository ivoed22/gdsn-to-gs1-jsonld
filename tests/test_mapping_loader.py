from gdsn_to_gs1_jsonld.mapping_loader import load_mapping


def test_mapping_loader_reads_mapping_yaml(mapping_path):
    mapping = load_mapping(mapping_path)
    assert mapping.metadata["version"] == "0.1.0"
    assert len(mapping.fields) == 9
    assert mapping.fields[0].id == "gtin"
    assert mapping.fields[0].xpath.endswith("[local-name()='gtin']")
