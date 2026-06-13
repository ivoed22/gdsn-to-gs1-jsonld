"""Canonical product models used between XML extraction and JSON-LD output."""

from decimal import Decimal

from pydantic import BaseModel, Field


class LanguageValue(BaseModel):
    value: str
    language: str


class MeasurementValue(BaseModel):
    value: Decimal | None = None
    unit_code: str | None = None


class AllergenDetail(BaseModel):
    allergen_type: str | None = None
    level_of_containment: str | None = None


class NutrientDetail(BaseModel):
    preparation_state_code: str | None = None
    nutrient_type_code: str | None = None
    quantity_contained: MeasurementValue | None = None


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
    ingredient_statement: list[LanguageValue] = Field(default_factory=list)
    allergens: list[AllergenDetail] = Field(default_factory=list)
    nutrients: list[NutrientDetail] = Field(default_factory=list)
