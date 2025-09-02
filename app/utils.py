"""Utility functions and helpers"""
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from flask import flash, redirect, url_for, request
import uuid
from datetime import datetime

# Money helper
TWOPL = Decimal("0.01")

def d(x):
    """Convert to Decimal with 2 decimal places"""
    if x is None:
        return Decimal("0.00")
    if isinstance(x, Decimal):
        return x.quantize(TWOPL, rounding=ROUND_HALF_UP)
    return Decimal(str(x)).quantize(TWOPL, rounding=ROUND_HALF_UP)

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def generate_ref_code(prefix, project_code=None):
    """Generate a unique reference code"""
    year = datetime.now().year
    uuid_part = str(uuid.uuid4())[:6].upper()
    if project_code:
        return f"{prefix}-{project_code[:6]}-{year}-{uuid_part}"
    return f"{prefix}-{year}-{uuid_part}"

class ValidationError(Exception):
    """Custom validation error"""
    pass

def paginate_query(query, page=1, per_page=20):
    """Paginate a SQLAlchemy query"""
    page = max(1, page)
    return query.paginate(page=page, per_page=per_page, error_out=False)

def format_date(date_obj):
    """Format date for display"""
    if not date_obj:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")

def parse_date(date_str):
    """Parse date string to date object"""
    if not date_str:
        return None
    from dateutil import parser
    return parser.parse(date_str).date()

def flash_success(message):
    """Flash success message"""
    flash(message, 'success')

def flash_error(message):
    """Flash error message"""
    flash(message, 'error')

def validate_shares(shares_list):
    """Validate that shares sum to 100%"""
    total = sum(d(share) for share in shares_list)
    if total != Decimal("100.00"):
        raise ValidationError(f"مجموع الحصص يجب أن يساوي 100% (الحالي: {total}%)")
    return True

def format_money(amount, currency="ج.م"):
    """Format money for display"""
    return f"{d(amount):,.2f} {currency}"