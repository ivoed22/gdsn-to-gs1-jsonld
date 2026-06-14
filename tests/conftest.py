from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_XML = ROOT / "examples" / "input" / "example_product.xml"
MAPPING = ROOT / "mapping" / "mapping_mvp.yaml"
MAPPING_V0_2 = ROOT / "mapping" / "mapping_v0_2.yaml"
MAPPING_V0_3 = ROOT / "mapping" / "mapping_v0_3.yaml"
SAMPLE_DIR = ROOT / "examples" / "input" / "samples"


@pytest.fixture
def example_xml_path() -> Path:
    return EXAMPLE_XML


@pytest.fixture
def mapping_path() -> Path:
    return MAPPING


@pytest.fixture
def mapping_v0_2_path() -> Path:
    return MAPPING_V0_2


@pytest.fixture
def mapping_v0_3_path() -> Path:
    return MAPPING_V0_3


@pytest.fixture
def sample_dir() -> Path:
    return SAMPLE_DIR
