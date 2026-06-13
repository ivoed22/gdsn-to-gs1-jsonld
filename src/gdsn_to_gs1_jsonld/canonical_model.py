"""Canonical product models used between XML extraction and JSON-LD output."""

from decimal import Decimal

from pydantic import BaseModel, Field


class LanguageValue(BaseModel):
    value: str
    language: str


class CanonicalProduct(BaseModel):
    gtin: str | None = None
    product_name: list[LanguageValue] = Field(default_factory=list)
    product_description: list[LanguageValue] = Field(default_factory=list)
    brand_name: str | None = None
    gpc_category_code: str | None = None
    net_content_value: Decimal | None = None
    net_content_unit: str | None = None
    product_image_url: list[str] = Field(default_factory=list)
    product_page_url: str | None = None
