from pathlib import Path

from gdsn_to_gs1_jsonld.converter import convert_xml_to_jsonld


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "mapping" / "mapping_v0_5.yaml"


def test_v0_5_emits_reviewed_structured_supplier_and_product_metadata():
    xml = b"""<root>
      <tradeItem>
        <gtin>08720938815706</gtin>
        <informationProviderOfTradeItem><gln>8719333058290</gln><partyName>Example Supplier</partyName></informationProviderOfTradeItem>
        <gdsnTradeItemClassification><gpcCategoryCode>10000468</gpcCategoryCode><gpcCategoryName>Supplements</gpcCategoryName></gdsnTradeItemClassification>
        <targetMarket><targetMarketCountryCode>528</targetMarketCountryCode></targetMarket>
        <tradeItemContactInformation><contactTypeCode>CXC</contactTypeCode><targetMarketCommunicationChannel><communicationChannel><communicationChannelCode>EMAIL</communicationChannelCode><communicationValue>support@example.com</communicationValue></communicationChannel></targetMarketCommunicationChannel></tradeItemContactInformation>
        <functionalName languageCode="nl">B12</functionalName><regulatedProductName languageCode="nl">B12</regulatedProductName><tradeItemDescription languageCode="nl">B12</tradeItemDescription>
        <packaging><packagingTypeCode>PO</packagingTypeCode></packaging>
        <countryOfOrigin><countryCode>528</countryCode></countryOfOrigin>
        <grossWeight measurementUnitCode="GRM">36</grossWeight>
        <referencedFileHeader><referencedFileTypeCode>PRODUCT_IMAGE</referencedFileTypeCode><fileName>image.jpg</fileName><uniformResourceIdentifier>https://example.com/image.jpg</uniformResourceIdentifier><referencedFileDetail><filePixelHeight>2500</filePixelHeight><filePixelWidth>2000</filePixelWidth></referencedFileDetail></referencedFileHeader>
      </tradeItem>
    </root>"""

    data = convert_xml_to_jsonld(xml, MAPPING).jsonld_data

    assert data["gs1:functionalName"][0]["@value"] == "B12"
    assert data["gs1:regulatedProductName"][0]["@language"] == "nl"
    assert data["gs1:grossWeight"]["gs1:value"] == 36
    assert data["gs1:packaging"][0]["gs1:packagingType"] == "PO"
    assert data["gs1:countryOfOrigin"][0]["gs1:countryCode"] == "528"
    assert data["gs1:targetMarket"][0]["gs1:targetMarketCountries"]["gs1:countryCode"] == "528"
    support = data["gs1:customerSupportCentre"][0]
    assert support["gs1:partyGLN"] == "8719333058290"
    assert support["gs1:contactPoint"]["gs1:email"] == "support@example.com"
    image = data["gs1:image"][0]
    assert image["gs1:filePixelHeight"] == 2500
    assert image["gs1:filePixelWidth"] == 2000
