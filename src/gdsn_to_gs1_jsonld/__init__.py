"""GDSN XML to GS1 Web Vocabulary JSON-LD converter."""

from .converter import ConversionResult, convert_xml_to_jsonld

__all__ = ["ConversionResult", "convert_xml_to_jsonld"]
__version__ = "0.1.0"
