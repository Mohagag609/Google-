"""Wallet management service"""
from db import db
from models import ProjectPartner, Voucher
from utils import d, generate_ref_code, ValidationError
from datetime import date
from decimal import Decimal

def deposit_to_wallet(project_id, partner_id, amount, notes=None):
    """Deposit money to partner wallet"""
    amount = d(amount)
    if amount <= 0:
        raise ValidationError("مبلغ الإيداع يجب أن يكون أكبر من صفر")
    
    # Find project partner
    pp = ProjectPartner.query.filter_by(
        project_id=project_id,
        partner_id=partner_id
    ).first()
    
    if not pp:
        raise ValidationError("الشريك غير مرتبط بالمشروع")
    
    # Create receipt voucher
    voucher = Voucher(
        project_id=project_id,
        v_type='receipt',
        party_type='partner',
        party_id=partner_id,
        amount=amount,
        v_date=date.today(),
        ref_code=generate_ref_code('RV', pp.project.code),
        notes=notes
    )
    
    # Update wallet balance
    pp.wallet_balance = d(pp.wallet_balance) + amount
    
    db.session.add(voucher)
    db.session.commit()
    
    return voucher

def withdraw_from_wallet(project_id, partner_id, amount, notes=None):
    """Withdraw money from partner wallet"""
    amount = d(amount)
    if amount <= 0:
        raise ValidationError("مبلغ السحب يجب أن يكون أكبر من صفر")
    
    # Find project partner
    pp = ProjectPartner.query.filter_by(
        project_id=project_id,
        partner_id=partner_id
    ).first()
    
    if not pp:
        raise ValidationError("الشريك غير مرتبط بالمشروع")
    
    # Check balance
    if d(pp.wallet_balance) < amount:
        raise ValidationError(f"الرصيد غير كافي. الرصيد الحالي: {d(pp.wallet_balance)}")
    
    # Create payment voucher
    voucher = Voucher(
        project_id=project_id,
        v_type='payment',
        party_type='partner',
        party_id=partner_id,
        amount=amount,
        v_date=date.today(),
        ref_code=generate_ref_code('PV', pp.project.code),
        notes=notes
    )
    
    # Update wallet balance
    pp.wallet_balance = d(pp.wallet_balance) - amount
    
    db.session.add(voucher)
    db.session.commit()
    
    return voucher

def get_wallet_balance(project_id, partner_id):
    """Get current wallet balance for partner"""
    pp = ProjectPartner.query.filter_by(
        project_id=project_id,
        partner_id=partner_id
    ).first()
    
    if not pp:
        return Decimal("0.00")
    
    return d(pp.wallet_balance)

def get_wallet_movements(project_id, partner_id, from_date=None, to_date=None):
    """Get wallet movements for a partner"""
    query = Voucher.query.filter_by(
        project_id=project_id,
        party_type='partner',
        party_id=partner_id
    )
    
    if from_date:
        query = query.filter(Voucher.v_date >= from_date)
    if to_date:
        query = query.filter(Voucher.v_date <= to_date)
    
    return query.order_by(Voucher.v_date.desc()).all()