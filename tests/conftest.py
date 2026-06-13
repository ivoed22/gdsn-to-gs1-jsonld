from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_XML = ROOT / "examples" / "input" / "example_product.xml"
MAPPING = ROOT / "mapping" / "mapping_mvp.yaml"


@pytest.fixture
def example_xml_path() -> Path:
    return EXAMPLE_XML


@pytest.fixture
def mapping_path() -> Path:
    return MAPPING
