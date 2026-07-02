import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Some machines cannot use the default pytest temp root
# (``<system temp>/pytest-of-<user>``) — e.g. a leftover directory with a
# restrictive ACL — which makes every ``tmp_path``-using test error out with
# ``PermissionError: [WinError 5]`` before it even runs. Point pytest at a
# writable, git-ignored repo-local temp root instead (honouring an explicit
# ``PYTEST_DEBUG_TEMPROOT`` if the environment already set one). This must run at
# conftest import time, before the first ``tmp_path`` fixture computes basetemp.
_PYTEST_TEMP_ROOT = ROOT / ".pytest-tmp"
_PYTEST_TEMP_ROOT.mkdir(exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_PYTEST_TEMP_ROOT))

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
