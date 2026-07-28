"""Canonical product models used between XML extraction and JSON-LD output."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class LanguageValue(BaseModel):
    value: str
    language: str


class MeasurementValue(BaseModel):
    value: Decimal | None = None
    unit_code: str | None = None


class BrandDetail(BaseModel):
    """Brand as its own node.

    gs1:brandName has domain gs1:Brand, so the name must hang off a Brand node
    reached via gs1:brand — asserting it directly on the product would imply
    the product is itself a Brand.
    """

    brand_name: LanguageValue | None = None


class AllergenDetail(BaseModel):
    allergen_type: str | None = None
    level_of_containment: str | None = None


class NutrientDetail(BaseModel):
    preparation_state_code: str | None = None
    nutrient_type_code: str | None = None
    quantity_contained: MeasurementValue | None = None


class CertificationDetail(BaseModel):
    certification_standard: str | None = None
    certification_identification: str | None = None
    certification_value: str | None = None
    certificate_issuance_date_time: str | None = None
    assessment_date: str | None = None
    effective_start: str | None = None
    effective_end: str | None = None
    certification_organisation_identifier: str | None = None


class ReferencedDocument(BaseModel):
    file_name: str | None = None
    file_format: str | None = None
    referenced_file_type: str | None = None
    document_url: str | None = None


class CanonicalProduct(BaseModel):
    gtin: str | None = None
    product_name: list[LanguageValue] = Field(default_factory=list)
    product_description: list[LanguageValue] = Field(default_factory=list)
    brand_name: str | None = None
    brands: list[BrandDetail] = Field(default_factory=list)
    gpc_category_code: str | None = None
    gpc_category_description: list[LanguageValue] = Field(default_factory=list)
    functional_name: list[LanguageValue] = Field(default_factory=list)
    regulated_product_name: list[LanguageValue] = Field(default_factory=list)
    net_content_value: Decimal | None = None
    net_content_unit: str | None = None
    product_image_url: list[str] = Field(default_factory=list)
    product_page_url: str | None = None
    ingredient_statement: list[LanguageValue] = Field(default_factory=list)
    allergens: list[AllergenDetail] = Field(default_factory=list)
    nutrients: list[NutrientDetail] = Field(default_factory=list)
    certifications: list[CertificationDetail] = Field(default_factory=list)
    referenced_documents: list[ReferencedDocument] = Field(default_factory=list)
    gross_weights: list[dict[str, Any]] = Field(default_factory=list)
    packaging_details: list[dict[str, Any]] = Field(default_factory=list)
    countries_of_origin: list[dict[str, Any]] = Field(default_factory=list)
    target_markets: list[dict[str, Any]] = Field(default_factory=list)
    customer_support_centres: list[dict[str, Any]] = Field(default_factory=list)
    product_images: list[dict[str, Any]] = Field(default_factory=list)
