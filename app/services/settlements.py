"""Settlement calculation and posting service"""
from db import db
from models import (
    Project, ProjectPartner, Expense, StockMove, Voucher,
    PartnerSettleBatch, PartnerSettleLine, PartnerClaim
)
from utils import d, ValidationError
from datetime import datetime
from decimal import Decimal

def calculate_total_project_cost(project_id, cutoff_date):
    """Calculate total project cost until cutoff date"""
    # Sum all expenses until cutoff
    expenses_total = db.session.query(
        db.func.sum(Expense.amount)
    ).filter(
        Expense.project_id == project_id,
        Expense.date <= cutoff_date
    ).scalar() or Decimal("0")
    
    # Sum all stock issues until cutoff
    stock_total = db.session.query(
        db.func.sum(StockMove.amount)
    ).filter(
        StockMove.project_id == project_id,
        StockMove.qty_out > 0,
        StockMove.move_date <= cutoff_date
    ).scalar() or Decimal("0")
    
    return d(expenses_total) + d(stock_total)

def calculate_partner_payments(project_id, partner_id, cutoff_date):
    """Calculate total payments made by partner until cutoff"""
    # Deposits (receipts from partner)
    deposits = db.session.query(
        db.func.sum(Voucher.amount)
    ).filter(
        Voucher.project_id == project_id,
        Voucher.party_type == 'partner',
        Voucher.party_id == partner_id,
        Voucher.v_type == 'receipt',
        Voucher.v_date <= cutoff_date
    ).scalar() or Decimal("0")
    
    # Withdrawals (payments to partner)
    withdrawals = db.session.query(
        db.func.sum(Voucher.amount)
    ).filter(
        Voucher.project_id == project_id,
        Voucher.party_type == 'partner',
        Voucher.party_id == partner_id,
        Voucher.v_type == 'payment',
        Voucher.v_date <= cutoff_date
    ).scalar() or Decimal("0")
    
    # Direct partner expenses
    direct_expenses = db.session.query(
        db.func.sum(Expense.amount)
    ).filter(
        Expense.project_id == project_id,
        Expense.payee_type == 'partner',
        Expense.payee_id == partner_id,
        Expense.date <= cutoff_date
    ).scalar() or Decimal("0")
    
    return d(deposits) - d(withdrawals) + d(direct_expenses)

def create_settlement_preview(project_id, cutoff_date):
    """Create settlement batch preview (not posted)"""
    project = Project.query.get(project_id)
    if not project:
        raise ValidationError("المشروع غير موجود")
    
    # Check for existing unposted batch
    existing = PartnerSettleBatch.query.filter_by(
        project_id=project_id,
        status='open'
    ).first()
    
    if existing:
        db.session.delete(existing)
        db.session.commit()
    
    # Calculate total project cost
    total_cost = calculate_total_project_cost(project_id, cutoff_date)
    
    # Create batch
    batch = PartnerSettleBatch(
        project_id=project_id,
        cutoff_date=cutoff_date,
        status='open',
        total_cost_until_cutoff=total_cost
    )
    db.session.add(batch)
    db.session.flush()
    
    # Create settlement lines for each partner
    partners = ProjectPartner.query.filter_by(project_id=project_id).all()
    
    creditors = []  # Partners who overpaid
    debtors = []    # Partners who underpaid
    
    for pp in partners:
        # Calculate what partner should bear
        should_bear = d(total_cost * pp.share_pct / 100)
        
        # Calculate what partner actually paid
        actually_paid = calculate_partner_payments(project_id, pp.partner_id, cutoff_date)
        
        # Calculate difference including carry forward
        diff = d(actually_paid - should_bear + pp.carry_forward_balance)
        
        # Create settlement line
        line = PartnerSettleLine(
            batch_id=batch.id,
            partner_id=pp.partner_id,
            share_pct_at_cutoff=pp.share_pct,
            should_bear_amount=should_bear,
            actually_paid_amount=actually_paid,
            diff_amount=diff
        )
        db.session.add(line)
        
        # Categorize for claims
        if diff > 0:
            creditors.append((pp.partner_id, diff))
        elif diff < 0:
            debtors.append((pp.partner_id, abs(diff)))
    
    # Create claims (greedy matching)
    create_claims(batch.id, creditors, debtors)
    
    db.session.commit()
    return batch

def create_claims(batch_id, creditors, debtors):
    """Create partner claims using greedy matching"""
    # Sort creditors and debtors by amount (descending)
    creditors = sorted(creditors, key=lambda x: x[1], reverse=True)
    debtors = sorted(debtors, key=lambda x: x[1], reverse=True)
    
    for debtor_id, debtor_amount in debtors:
        remaining = debtor_amount
        
        for i, (creditor_id, creditor_amount) in enumerate(creditors):
            if creditor_amount <= 0:
                continue
            
            # Calculate claim amount
            claim_amount = min(remaining, creditor_amount)
            
            if claim_amount > 0:
                # Create claim
                claim = PartnerClaim(
                    batch_id=batch_id,
                    from_partner_id=debtor_id,
                    to_partner_id=creditor_id,
                    amount=claim_amount,
                    status='pending'
                )
                db.session.add(claim)
                
                # Update remaining amounts
                remaining -= claim_amount
                creditors[i] = (creditor_id, creditor_amount - claim_amount)
            
            if remaining <= 0:
                break

def post_settlement(batch_id):
    """Post settlement batch and update carry forward balances"""
    batch = PartnerSettleBatch.query.get(batch_id)
    if not batch:
        raise ValidationError("دفعة التسوية غير موجودة")
    
    if batch.status == 'posted':
        raise ValidationError("دفعة التسوية تم ترحيلها بالفعل")
    
    # Update carry forward balances
    for line in batch.lines:
        pp = ProjectPartner.query.filter_by(
            project_id=batch.project_id,
            partner_id=line.partner_id
        ).first()
        
        if pp:
            pp.carry_forward_balance = d(pp.carry_forward_balance) + d(line.diff_amount)
    
    # Mark batch as posted
    batch.status = 'posted'
    batch.posted_at = datetime.utcnow()
    
    db.session.commit()
    return batch

def reverse_settlement(batch_id):
    """Reverse a posted settlement"""
    batch = PartnerSettleBatch.query.get(batch_id)
    if not batch:
        raise ValidationError("دفعة التسوية غير موجودة")
    
    if batch.status != 'posted':
        raise ValidationError("يمكن عكس الدفعات المرحلة فقط")
    
    # Reverse carry forward balances
    for line in batch.lines:
        pp = ProjectPartner.query.filter_by(
            project_id=batch.project_id,
            partner_id=line.partner_id
        ).first()
        
        if pp:
            pp.carry_forward_balance = d(pp.carry_forward_balance) - d(line.diff_amount)
    
    # Mark batch as reversed
    batch.status = 'reversed'
    
    db.session.commit()
    return batch