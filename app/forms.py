#!/usr/bin/env python3
"""
Form validation for Musharaka Pro
"""

from decimal import Decimal
from typing import Dict, Any, List
from utils import d, ValidationError

class FormValidator:
    """Simple form validator."""
    
    @staticmethod
    def validate_required(data: Dict[str, Any], fields: List[str]) -> None:
        """Validate required fields."""
        for field in fields:
            if field not in data or not data[field]:
                raise ValidationError(f"الحقل {field} مطلوب")
    
    @staticmethod
    def validate_decimal(value: Any, min_val: Decimal = None, max_val: Decimal = None) -> Decimal:
        """Validate and convert to decimal."""
        try:
            decimal_val = d(value)
            if min_val is not None and decimal_val < min_val:
                raise ValidationError(f"القيمة يجب أن تكون أكبر من أو تساوي {min_val}")
            if max_val is not None and decimal_val > max_val:
                raise ValidationError(f"القيمة يجب أن تكون أقل من أو تساوي {max_val}")
            return decimal_val
        except (ValueError, TypeError):
            raise ValidationError("قيمة رقمية غير صحيحة")
    
    @staticmethod
    def validate_percentage(value: Any) -> Decimal:
        """Validate percentage (0-100)."""
        return FormValidator.validate_decimal(value, Decimal('0'), Decimal('100'))
    
    @staticmethod
    def validate_positive_decimal(value: Any) -> Decimal:
        """Validate positive decimal."""
        return FormValidator.validate_decimal(value, Decimal('0'))

class ProjectForm:
    """Project form validation."""
    
    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project creation data."""
        FormValidator.validate_required(data, ['code', 'name'])
        
        return {
            'code': data['code'].strip(),
            'name': data['name'].strip(),
            'base_currency': data.get('base_currency', 'EGP').strip()
        }

class PartnerForm:
    """Partner form validation."""
    
    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate partner creation data."""
        FormValidator.validate_required(data, ['name'])
        
        return {
            'name': data['name'].strip()
        }
    
    @staticmethod
    def validate_link(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate partner link data."""
        FormValidator.validate_required(data, ['partner_id', 'share_pct'])
        
        return {
            'partner_id': data['partner_id'].strip(),
            'share_pct': FormValidator.validate_percentage(data['share_pct'])
        }

class WalletForm:
    """Wallet form validation."""
    
    @staticmethod
    def validate_transaction(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate wallet transaction data."""
        FormValidator.validate_required(data, ['amount'])
        
        return {
            'amount': FormValidator.validate_positive_decimal(data['amount']),
            'notes': data.get('notes', '').strip()
        }

class StageForm:
    """Stage form validation."""
    
    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stage creation data."""
        FormValidator.validate_required(data, ['name'])
        
        return {
            'name': data['name'].strip(),
            'budget': FormValidator.validate_positive_decimal(data.get('budget', 0))
        }

class PurchaseForm:
    """Purchase form validation."""
    
    @staticmethod
    def validate_invoice(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate purchase invoice data."""
        FormValidator.validate_required(data, ['supplier_id', 'date', 'items'])
        
        if not isinstance(data['items'], list) or not data['items']:
            raise ValidationError("يجب إضافة عنصر واحد على الأقل")
        
        validated_items = []
        for item in data['items']:
            FormValidator.validate_required(item, ['item_id', 'qty', 'unit_cost', 'warehouse_id'])
            
            validated_items.append({
                'item_id': item['item_id'].strip(),
                'qty': FormValidator.validate_positive_decimal(item['qty']),
                'unit_cost': FormValidator.validate_positive_decimal(item['unit_cost']),
                'tax': FormValidator.validate_positive_decimal(item.get('tax', 0)),
                'warehouse_id': item['warehouse_id'].strip()
            })
        
        return {
            'supplier_id': data['supplier_id'].strip(),
            'date': data['date'],
            'items': validated_items
        }

class StockForm:
    """Stock form validation."""
    
    @staticmethod
    def validate_issue(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stock issue data."""
        FormValidator.validate_required(data, ['warehouse_id', 'item_id', 'qty', 'stage_id'])
        
        return {
            'warehouse_id': data['warehouse_id'].strip(),
            'item_id': data['item_id'].strip(),
            'qty': FormValidator.validate_positive_decimal(data['qty']),
            'stage_id': data['stage_id'].strip()
        }

class ExpenseForm:
    """Expense form validation."""
    
    @staticmethod
    def validate_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate expense creation data."""
        FormValidator.validate_required(data, ['amount', 'description', 'date'])
        
        return {
            'amount': FormValidator.validate_positive_decimal(data['amount']),
            'description': data['description'].strip(),
            'date': data['date'],
            'stage_id': data.get('stage_id'),
            'payee_type': data.get('payee_type', 'other'),
            'payee_id': data.get('payee_id')
        }

class AllocationForm:
    """Allocation form validation."""
    
    @staticmethod
    def validate_custom(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate custom allocation data."""
        if 'partner_amounts' not in data or not isinstance(data['partner_amounts'], dict):
            raise ValidationError("يجب تحديد مبالغ الشركاء")
        
        partner_amounts = {}
        for partner_id, amount in data['partner_amounts'].items():
            partner_amounts[partner_id.strip()] = FormValidator.validate_positive_decimal(amount)
        
        return {
            'partner_amounts': partner_amounts
        }

class SettlementForm:
    """Settlement form validation."""
    
    @staticmethod
    def validate_batch(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settlement batch data."""
        FormValidator.validate_required(data, ['cutoff_date'])
        
        return {
            'cutoff_date': data['cutoff_date'],
            'notes': data.get('notes', '').strip()
        }