"""Small transformation and validation utilities."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_valid_gtin(value: str) -> bool:
    if len(value) not in {8, 12, 13, 14} or not value.isdigit():
        return False
    digits = [int(digit) for digit in value]
    weighted_sum = sum(
        digit * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(digits[:-1]))
    )
    expected = (10 - weighted_sum % 10) % 10
    return digits[-1] == expected


def apply_transform(value: str, transform: str) -> str | Decimal:
    if transform == "trim":
        return value.strip()
    if transform == "normalize_whitespace":
        return normalize_whitespace(value)
    if transform == "uppercase":
        return value.upper()
    if transform == "to_decimal":
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"'{value}' is not a decimal") from exc
    if transform == "to_date":
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).date().isoformat()
            except ValueError as exc:
                raise ValueError(f"'{value}' is not an ISO date or datetime") from exc
    if transform == "validate_gtin":
        if not is_valid_gtin(value):
            raise ValueError(f"'{value}' is not a valid GTIN")
        return value
    if transform == "validate_url":
        if not is_valid_url(value):
            raise ValueError(f"'{value}' is not a valid HTTP(S) URL")
        return value
    raise ValueError(f"Unknown transform: {transform}")


def serializable_value(value: object) -> object:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral() else float(value)
    return value
