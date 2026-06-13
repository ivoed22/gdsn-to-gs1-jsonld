"""Load and validate configurable XML-to-canonical mappings."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class MappingField(BaseModel):
    id: str
    description: str
    xpath: str
    value_xpath: str = "text()"
    language_xpath: str | None = None
    canonical_field: str
    jsonld_property: str
    required: bool = False
    datatype: str = "string"
    multiple: bool = False
    fallback_language: str | None = None
    transform: list[str] = Field(default_factory=list)


class MappingSettings(BaseModel):
    namespace_strategy: str = "local-name"
    default_language: str = "en"
    jsonld_context: list[Any] = Field(default_factory=list)


class MappingConfig(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    settings: MappingSettings
    fields: list[MappingField]


def load_mapping(mapping_path: str | Path) -> MappingConfig:
    path = Path(mapping_path)
    if not path.is_file():
        raise FileNotFoundError(f"Mapping file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Mapping file must contain a YAML object: {path}")
    return MappingConfig.model_validate(data)
