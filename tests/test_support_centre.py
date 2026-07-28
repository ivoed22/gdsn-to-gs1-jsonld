"""Regression tests for the customer-support-centre identity fix (issue #13).

The v0.6 profile used to read `partyGLN` and `organizationName` from
`informationProviderOfTradeItem` while the surrounding object was built from a
`tradeItemContactInformation` block. That asserted "the support centre is the
data provider", which GDSN never states.
"""

import pathlib

import yaml

V0_6 = pathlib.Path("mapping/mapping_v0_6.yaml")


def _support_mapping():
    profile = yaml.safe_load(V0_6.read_text(encoding="utf-8"))
    for object_mapping in profile["object_mappings"]:
        if object_mapping["id"] == "customer_support_centres":
            return object_mapping
    raise AssertionError("customer_support_centres mapping missing")


def test_support_identity_is_not_taken_from_information_provider():
    """The core defect: no field may reach out to informationProviderOfTradeItem."""
    mapping = _support_mapping()
    for field in mapping["fields"]:
        assert "informationProviderOfTradeItem" not in field["xpath"], (
            f"{field['id']} borrows identity from the information provider; "
            "support-centre identity must come from the contact block itself"
        )


def test_support_gln_comes_from_the_contact_block():
    mapping = _support_mapping()
    gln = next(f for f in mapping["fields"] if f["jsonld_property"] == "gs1:partyGLN")
    # tradeItemContactInformation carries its own gln
    assert gln["xpath"] == "./*[local-name()='gln']"


def test_no_organization_name_is_fabricated():
    """GDSN's contact block has no party name; emitting none beats a borrowed one."""
    mapping = _support_mapping()
    properties = {f["jsonld_property"] for f in mapping["fields"]}
    assert "gs1:organizationName" not in properties


def test_support_contact_point_is_still_populated():
    """The fix must not throw away the contact details themselves."""
    mapping = _support_mapping()
    properties = {f["jsonld_property"] for f in mapping["fields"]}
    assert "gs1:contactPoint.schema:name" in properties
    assert "gs1:contactPoint.gs1:email" in properties
