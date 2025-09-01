#!/usr/bin/env python3
"""
Utility functions for Musharaka Pro
"""

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

# Decimal precision constant
TWOPL = Decimal("0.01")

def d(x: Optional[Union[str, int, float, Decimal]]) -> Decimal:
    """Convert value to Decimal with 2 decimal places precision."""
    if x is None:
        return Decimal("0.00")
    if isinstance(x, Decimal):
        return x.quantize(TWOPL)
    return Decimal(str(x)).quantize(TWOPL, rounding=ROUND_HALF_UP)

def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())

def format_currency(amount: Decimal, currency: str = "EGP") -> str:
    """Format decimal amount as currency string."""
    return f"{amount:,.2f} {currency}"

def format_percentage(value: Decimal) -> str:
    """Format decimal as percentage."""
    return f"{value:.2f}%"

def validate_shares_total(shares: list[Decimal], tolerance: Decimal = Decimal("0.01")) -> bool:
    """Validate that shares sum to 100% within tolerance."""
    total = sum(shares)
    return abs(total - Decimal("100.00")) <= tolerance

def calculate_share_amount(total: Decimal, share_pct: Decimal) -> Decimal:
    """Calculate amount based on share percentage."""
    return d(total * share_pct / Decimal("100.00"))

class ValidationError(Exception):
    """Custom validation error."""
    pass

class BusinessRuleError(Exception):
    """Custom business rule error."""
    pass