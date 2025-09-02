"""Cost allocation service"""
from db import db
from models import Stage, Expense, StockMove, Allocation, ProjectPartner
from utils import d, ValidationError
from datetime import date
from decimal import Decimal
import json

def get_stage_total_cost(stage_id):
    """Calculate total cost for a stage"""
    stage = Stage.query.get(stage_id)
    if not stage:
        raise ValidationError("المرحلة غير موجودة")
    
    # Sum expenses for this stage
    expenses_total = db.session.query(
        db.func.sum(Expense.amount)
    ).filter_by(stage_id=stage_id).scalar() or Decimal("0")
    
    # Sum stock moves (issues) for this stage
    stock_total = db.session.query(
        db.func.sum(StockMove.amount)
    ).filter(
        StockMove.stage_id == stage_id,
        StockMove.qty_out > 0
    ).scalar() or Decimal("0")
    
    return d(expenses_total) + d(stock_total)

def get_stage_allocated_amount(stage_id):
    """Get already allocated amount for a stage"""
    allocated = db.session.query(
        db.func.sum(Allocation.total_amount)
    ).filter(
        Allocation.stage_id == stage_id,
        Allocation.posted == True
    ).scalar() or Decimal("0")
    
    return d(allocated)

def calculate_delta(stage_id):
    """Calculate delta (unallocated cost) for a stage"""
    total = get_stage_total_cost(stage_id)
    allocated = get_stage_allocated_amount(stage_id)
    return d(total - allocated)

def allocate_by_share(stage_id):
    """Allocate stage costs by partner shares"""
    stage = Stage.query.get(stage_id)
    if not stage:
        raise ValidationError("المرحلة غير موجودة")
    
    # Calculate delta
    delta = calculate_delta(stage_id)
    if delta <= 0:
        raise ValidationError("لا توجد تكاليف جديدة للتوزيع")
    
    # Get project partners
    partners = ProjectPartner.query.filter_by(project_id=stage.project_id).all()
    if not partners:
        raise ValidationError("لا يوجد شركاء في المشروع")
    
    # Validate shares sum to 100%
    total_shares = sum(d(p.share_pct) for p in partners)
    if total_shares != Decimal("100.00"):
        raise ValidationError(f"مجموع حصص الشركاء يجب أن يساوي 100% (الحالي: {total_shares}%)")
    
    # Calculate allocation per partner
    details = {}
    total_allocated = Decimal("0.00")
    
    for i, partner in enumerate(partners):
        share = d(partner.share_pct)
        # For last partner, allocate remaining to avoid rounding issues
        if i == len(partners) - 1:
            amount = delta - total_allocated
        else:
            amount = d(delta * share / 100)
        
        # Check wallet balance
        if d(partner.wallet_balance) < amount:
            raise ValidationError(
                f"رصيد المحفظة غير كافي للشريك {partner.partner.name}. "
                f"المطلوب: {amount}, المتاح: {d(partner.wallet_balance)}"
            )
        
        details[partner.partner_id] = str(amount)
        total_allocated += amount
    
    # Create allocation record
    allocation = Allocation(
        project_id=stage.project_id,
        stage_id=stage_id,
        rule='by_share',
        details_json=json.dumps(details),
        total_amount=delta,
        posted=True,
        alloc_date=date.today()
    )
    
    # Deduct from wallets
    for partner in partners:
        amount = d(details[partner.partner_id])
        partner.wallet_balance = d(partner.wallet_balance) - amount
    
    db.session.add(allocation)
    db.session.commit()
    
    return allocation

def allocate_custom(stage_id, custom_amounts):
    """Allocate stage costs with custom amounts"""
    stage = Stage.query.get(stage_id)
    if not stage:
        raise ValidationError("المرحلة غير موجودة")
    
    # Calculate delta
    delta = calculate_delta(stage_id)
    if delta <= 0:
        raise ValidationError("لا توجد تكاليف جديدة للتوزيع")
    
    # Validate custom amounts sum to delta
    total_custom = sum(d(amount) for amount in custom_amounts.values())
    if total_custom != delta:
        raise ValidationError(
            f"مجموع المبالغ المخصصة ({total_custom}) يجب أن يساوي التكلفة غير الموزعة ({delta})"
        )
    
    # Check wallet balances
    for partner_id, amount in custom_amounts.items():
        pp = ProjectPartner.query.filter_by(
            project_id=stage.project_id,
            partner_id=partner_id
        ).first()
        
        if not pp:
            raise ValidationError(f"الشريك {partner_id} غير مرتبط بالمشروع")
        
        if d(pp.wallet_balance) < d(amount):
            raise ValidationError(
                f"رصيد المحفظة غير كافي للشريك {pp.partner.name}. "
                f"المطلوب: {d(amount)}, المتاح: {d(pp.wallet_balance)}"
            )
    
    # Create allocation record
    details = {pid: str(d(amt)) for pid, amt in custom_amounts.items()}
    allocation = Allocation(
        project_id=stage.project_id,
        stage_id=stage_id,
        rule='custom',
        details_json=json.dumps(details),
        total_amount=delta,
        posted=True,
        alloc_date=date.today()
    )
    
    # Deduct from wallets
    for partner_id, amount in custom_amounts.items():
        pp = ProjectPartner.query.filter_by(
            project_id=stage.project_id,
            partner_id=partner_id
        ).first()
        pp.wallet_balance = d(pp.wallet_balance) - d(amount)
    
    db.session.add(allocation)
    db.session.commit()
    
    return allocation

def get_stage_allocations(stage_id):
    """Get all allocations for a stage"""
    return Allocation.query.filter_by(stage_id=stage_id).order_by(Allocation.alloc_date.desc()).all()