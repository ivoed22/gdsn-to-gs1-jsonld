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
    # Optional strict typing: emit {"@value": ..., "@type": <value_datatype>}
    # instead of a bare literal, for properties whose WebVoc range is not a
    # plain string (e.g. xsd:float, xsd:dateTime, xsd:anyURI). Opt-in: omitting
    # it keeps the previous, untyped output byte-for-byte.
    value_datatype: str | None = None
    transform: list[str] = Field(default_factory=list)


class ObjectMappingField(BaseModel):
    id: str
    xpath: str
    value_xpath: str = "text()"
    language_xpath: str | None = None
    canonical_field: str | None = None
    jsonld_property: str
    datatype: str = "string"
    required: bool = False
    multiple: bool = False
    fallback_language: str | None = None
    code_prefix: str | None = None
    nested_object_type: str | None = None
    value_datatype: str | None = None
    transform: list[str] = Field(default_factory=list)


class ObjectMapping(BaseModel):
    id: str
    description: str
    parent_xpath: str
    canonical_field: str
    jsonld_property: str
    object_type: str | None = None
    multiple: bool = True
    fields: list[ObjectMappingField]


class MappingSettings(BaseModel):
    namespace_strategy: str = "local-name"
    default_language: str = "en"
    jsonld_context: list[Any] = Field(default_factory=list)
    # Root @type for the generated document. Defaults to gs1:Product; a profile
    # that emits subclass-specific properties (e.g. gs1:ingredientStatement,
    # whose domain is gs1:FoodBeverageTobaccoProduct) can declare the more
    # specific class so consumers without RDFS inference still see it.
    root_type: str = "gs1:Product"


class MappingConfig(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    settings: MappingSettings
    fields: list[MappingField]
    object_mappings: list[ObjectMapping] = Field(default_factory=list)


def load_mapping(mapping_path: str | Path) -> MappingConfig:
    path = Path(mapping_path)
    if not path.is_file():
        raise FileNotFoundError(f"Mapping file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Mapping file must contain a YAML object: {path}")
    return MappingConfig.model_validate(data)
