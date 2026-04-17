"""Validators to guard against NaN, Infinity and divide-by-zero."""

from __future__ import annotations

import math


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide *numerator* by *denominator*, returning *default* when the
    denominator is zero or the result is not finite."""
    if denominator == 0:
        return default
    result = numerator / denominator
    if not math.isfinite(result):
        return default
    return result


def clamp_positive(value: float, fallback: float = 1.0) -> float:
    """Ensure *value* is a positive finite number, else return *fallback*."""
    if not math.isfinite(value) or value <= 0:
        return fallback
    return value
