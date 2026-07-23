from pathlib import Path

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "mapping" / "mapping_v0_6.yaml"


def test_v0_6_emits_explicit_codes_and_typed_nested_objects():
    xml = b"""<root><tradeItem>
      <gtin>08720938815706</gtin>
      <informationProviderOfTradeItem><gln>8719333058290</gln><partyName>Example Supplier</partyName></informationProviderOfTradeItem>
      <targetMarket><targetMarketCountryCode>528</targetMarketCountryCode></targetMarket>
      <tradeItemContactInformation><contactTypeCode>CXC</contactTypeCode><contactName>Marc Pronk</contactName><targetMarketCommunicationChannel><communicationChannel><communicationChannelCode>EMAIL</communicationChannelCode><communicationValue>support@example.com</communicationValue></communicationChannel></targetMarketCommunicationChannel></tradeItemContactInformation>
      <allergenRelatedInformation><allergen><allergenTypeCode>AU</allergenTypeCode><levelOfContainmentCode>CONTAINS</levelOfContainmentCode></allergen></allergenRelatedInformation>
      <packaging><packagingTypeCode>PO</packagingTypeCode></packaging>
      <referencedFileHeader><referencedFileTypeCode>PRODUCT_IMAGE</referencedFileTypeCode><uniformResourceIdentifier>https://example.com/image.jpg</uniformResourceIdentifier></referencedFileHeader>
    </tradeItem></root>"""

    data = convert_xml_to_jsonld(xml, MAPPING).jsonld_data

    allergen = data["gs1:hasAllergen"][0]
    assert allergen["gs1:allergenType"] == {"@id": "gs1:AllergenTypeCode-AU"}
    assert allergen["gs1:allergenLevelOfContainmentCode"] == {
        "@id": "gs1:LevelOfContainmentCode-CONTAINS"
    }
    assert data["gs1:packaging"][0]["gs1:packagingType"] == "PO"
    country = data["gs1:targetMarket"][0]["gs1:targetMarketCountries"]
    assert country == {"@type": "gs1:Country", "gs1:countryCode": "528"}
    contact = data["gs1:customerSupportCentre"][0]["gs1:contactPoint"]
    assert contact == {
        "@type": "gs1:ContactPoint",
        "schema:name": "Marc Pronk",
        "gs1:email": "support@example.com",
    }
    image = data["gs1:image"][0]
    assert image["gs1:referencedFileType"] == {
        "@id": "gs1:ReferencedFileTypeCode-PRODUCT_IMAGE"
    }
