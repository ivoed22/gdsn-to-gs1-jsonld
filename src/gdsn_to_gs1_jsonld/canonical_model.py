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
    gpc_category_code: str | None = None
    net_content_value: Decimal | None = None
    net_content_unit: str | None = None
    product_image_url: list[str] = Field(default_factory=list)
    product_page_url: str | None = None
    ingredient_statement: list[LanguageValue] = Field(default_factory=list)
    allergens: list[AllergenDetail] = Field(default_factory=list)
    nutrients: list[NutrientDetail] = Field(default_factory=list)
    certifications: list[CertificationDetail] = Field(default_factory=list)
    referenced_documents: list[ReferencedDocument] = Field(default_factory=list)
