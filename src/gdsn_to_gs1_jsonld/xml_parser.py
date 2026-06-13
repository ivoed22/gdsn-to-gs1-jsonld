"""Secure XML parsing helpers."""

from pathlib import Path
from typing import BinaryIO

from lxml import etree


class XMLParseError(ValueError):
    """Raised when input cannot be parsed as XML."""


XMLInput = str | bytes | bytearray | Path | BinaryIO


def parse_xml(xml_input: XMLInput) -> etree._Element:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=False,
        remove_blank_text=False,
    )
    try:
        if isinstance(xml_input, Path):
            return etree.parse(str(xml_input), parser).getroot()
        if isinstance(xml_input, str):
            candidate = Path(xml_input)
            if "<" not in xml_input and candidate.is_file():
                return etree.parse(str(candidate), parser).getroot()
            return etree.fromstring(xml_input.encode("utf-8"), parser)
        if isinstance(xml_input, (bytes, bytearray)):
            return etree.fromstring(bytes(xml_input), parser)
        return etree.parse(xml_input, parser).getroot()
    except (etree.XMLSyntaxError, OSError, ValueError) as exc:
        raise XMLParseError(f"Invalid XML: {exc}") from exc
