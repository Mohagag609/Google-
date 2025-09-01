#!/usr/bin/env python3
"""
Business logic services for Musharaka Pro
"""

import json
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

from db import db
from models import (
    Project, Partner, ProjectPartner, Supplier, Item, Warehouse, Stage,
    PurchaseInvoice, PurchaseInvoiceItem, StockMove, Expense, Voucher,
    Allocation, PartnerSettleBatch, PartnerSettleLine, PartnerClaim
)
from utils import d, generate_uuid, ValidationError, BusinessRuleError

class ProjectService:
    """Service for project operations."""
    
    @staticmethod
    def create_project(code: str, name: str, base_currency: str = 'EGP') -> Project:
        """Create a new project."""
        project = Project(
            code=code,
            name=name,
            base_currency=base_currency
        )
        db.session.add(project)
        db.session.commit()
        return project
    
    @staticmethod
    def get_project(project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return Project.query.get(project_id)
    
    @staticmethod
    def get_all_projects() -> List[Project]:
        """Get all projects."""
        return Project.query.all()

class PartnerService:
    """Service for partner operations."""
    
    @staticmethod
    def create_partner(name: str) -> Partner:
        """Create a new partner."""
        partner = Partner(name=name)
        db.session.add(partner)
        db.session.commit()
        return partner
    
    @staticmethod
    def get_all_partners() -> List[Partner]:
        """Get all partners."""
        return Partner.query.all()
    
    @staticmethod
    def link_partner_to_project(project_id: str, partner_id: str, share_pct: Decimal) -> ProjectPartner:
        """Link partner to project with share percentage."""
        # Validate shares don't exceed 100%
        existing_shares = db.session.query(func.sum(ProjectPartner.share_pct)).filter(
            ProjectPartner.project_id == project_id
        ).scalar() or Decimal('0')
        
        if existing_shares + share_pct > Decimal('100'):
            raise ValidationError("مجموع النسب لا يمكن أن يتجاوز 100%")
        
        project_partner = ProjectPartner(
            project_id=project_id,
            partner_id=partner_id,
            share_pct=share_pct
        )
        db.session.add(project_partner)
        db.session.commit()
        return project_partner
    
    @staticmethod
    def get_project_partners(project_id: str) -> List[ProjectPartner]:
        """Get all partners for a project."""
        return ProjectPartner.query.filter_by(project_id=project_id).all()

class WalletService:
    """Service for wallet operations."""
    
    @staticmethod
    def deposit(project_id: str, partner_id: str, amount: Decimal, notes: str = None) -> Voucher:
        """Deposit money to partner wallet."""
        project_partner = ProjectPartner.query.filter_by(
            project_id=project_id, partner_id=partner_id
        ).first()
        
        if not project_partner:
            raise ValidationError("الشريك غير مرتبط بهذا المشروع")
        
        # Update wallet balance
        project_partner.wallet_balance += amount
        
        # Create voucher
        voucher = Voucher(
            project_id=project_id,
            v_type='receipt',
            party_type='partner',
            party_id=partner_id,
            amount=amount,
            v_date=date.today(),
            ref_code=f"DEP-{generate_uuid()[:8]}",
            notes=notes
        )
        
        db.session.add(voucher)
        db.session.commit()
        return voucher
    
    @staticmethod
    def withdraw(project_id: str, partner_id: str, amount: Decimal, notes: str = None) -> Voucher:
        """Withdraw money from partner wallet."""
        project_partner = ProjectPartner.query.filter_by(
            project_id=project_id, partner_id=partner_id
        ).first()
        
        if not project_partner:
            raise ValidationError("الشريك غير مرتبط بهذا المشروع")
        
        if project_partner.wallet_balance < amount:
            raise BusinessRuleError("رصيد المحفظة غير كافي")
        
        # Update wallet balance
        project_partner.wallet_balance -= amount
        
        # Create voucher
        voucher = Voucher(
            project_id=project_id,
            v_type='payment',
            party_type='partner',
            party_id=partner_id,
            amount=amount,
            v_date=date.today(),
            ref_code=f"WTH-{generate_uuid()[:8]}",
            notes=notes
        )
        
        db.session.add(voucher)
        db.session.commit()
        return voucher

class StageService:
    """Service for stage operations."""
    
    @staticmethod
    def create_stage(project_id: str, name: str, budget: Decimal = Decimal('0')) -> Stage:
        """Create a new stage."""
        stage = Stage(
            project_id=project_id,
            name=name,
            budget=budget
        )
        db.session.add(stage)
        db.session.commit()
        return stage
    
    @staticmethod
    def get_stage_cost(stage_id: str) -> Dict[str, Decimal]:
        """Calculate stage total cost."""
        stage = Stage.query.get(stage_id)
        if not stage:
            raise ValidationError("المرحلة غير موجودة")
        
        # Direct expenses
        direct_expenses = db.session.query(func.sum(Expense.amount)).filter(
            and_(Expense.stage_id == stage_id, Expense.amount.isnot(None))
        ).scalar() or Decimal('0')
        
        # Stock issues (valued at std_cost)
        stock_issues = db.session.query(func.sum(StockMove.amount)).filter(
            and_(StockMove.stage_id == stage_id, StockMove.qty_out > 0)
        ).scalar() or Decimal('0')
        
        total_cost = d(direct_expenses + stock_issues)
        
        # Already allocated
        allocated = db.session.query(func.sum(Allocation.total_amount)).filter(
            and_(Allocation.stage_id == stage_id, Allocation.posted == True)
        ).scalar() or Decimal('0')
        
        delta = total_cost - allocated
        
        return {
            'direct_expenses': d(direct_expenses),
            'stock_issues': d(stock_issues),
            'total_cost': total_cost,
            'allocated': d(allocated),
            'delta': delta
        }

class AllocationService:
    """Service for cost allocation operations."""
    
    @staticmethod
    def allocate_by_share(stage_id: str) -> Allocation:
        """Allocate stage cost by partner shares."""
        stage = Stage.query.get(stage_id)
        if not stage:
            raise ValidationError("المرحلة غير موجودة")
        
        cost_info = StageService.get_stage_cost(stage_id)
        delta = cost_info['delta']
        
        if delta <= 0:
            raise BusinessRuleError("لا توجد تكلفة جديدة للتوزيع")
        
        # Get project partners
        project_partners = ProjectPartner.query.filter_by(project_id=stage.project_id).all()
        
        if not project_partners:
            raise BusinessRuleError("لا يوجد شركاء في المشروع")
        
        # Calculate allocations
        allocations = []
        total_allocated = Decimal('0')
        
        for pp in project_partners:
            amount = d(delta * pp.share_pct / Decimal('100'))
            allocations.append((pp.partner_id, amount))
            total_allocated += amount
        
        # Create allocation record
        allocation = Allocation(
            project_id=stage.project_id,
            stage_id=stage_id,
            rule='by_share',
            total_amount=total_allocated,
            posted=True,
            alloc_date=date.today()
        )
        
        db.session.add(allocation)
        
        # Update partner wallets
        for partner_id, amount in allocations:
            project_partner = ProjectPartner.query.filter_by(
                project_id=stage.project_id, partner_id=partner_id
            ).first()
            if project_partner:
                project_partner.wallet_balance -= amount
        
        db.session.commit()
        return allocation
    
    @staticmethod
    def allocate_custom(stage_id: str, partner_amounts: Dict[str, Decimal]) -> Allocation:
        """Allocate stage cost with custom amounts."""
        stage = Stage.query.get(stage_id)
        if not stage:
            raise ValidationError("المرحلة غير موجودة")
        
        cost_info = StageService.get_stage_cost(stage_id)
        delta = cost_info['delta']
        
        if delta <= 0:
            raise BusinessRuleError("لا توجد تكلفة جديدة للتوزيع")
        
        # Validate custom amounts sum to delta
        total_custom = sum(partner_amounts.values())
        if abs(total_custom - delta) > Decimal('0.01'):
            raise ValidationError("مجموع المبالغ المخصصة يجب أن يساوي التكلفة المتبقية")
        
        # Create allocation record
        allocation = Allocation(
            project_id=stage.project_id,
            stage_id=stage_id,
            rule='custom',
            details_json=json.dumps(partner_amounts),
            total_amount=total_custom,
            posted=True,
            alloc_date=date.today()
        )
        
        db.session.add(allocation)
        
        # Update partner wallets
        for partner_id, amount in partner_amounts.items():
            project_partner = ProjectPartner.query.filter_by(
                project_id=stage.project_id, partner_id=partner_id
            ).first()
            if project_partner:
                project_partner.wallet_balance -= amount
        
        db.session.commit()
        return allocation

class PurchaseService:
    """Service for purchase operations."""
    
    @staticmethod
    def create_invoice(project_id: str, supplier_id: str, invoice_date: date, items: List[Dict]) -> PurchaseInvoice:
        """Create purchase invoice with items."""
        invoice = PurchaseInvoice(
            project_id=project_id,
            supplier_id=supplier_id,
            date=invoice_date
        )
        db.session.add(invoice)
        db.session.flush()  # Get invoice ID
        
        total = Decimal('0')
        
        for item_data in items:
            item = Item.query.get(item_data['item_id'])
            if not item:
                raise ValidationError(f"الصنف غير موجود: {item_data['item_id']}")
            
            invoice_item = PurchaseInvoiceItem(
                invoice_id=invoice.id,
                item_id=item_data['item_id'],
                qty=d(item_data['qty']),
                unit_cost=d(item_data['unit_cost']),
                tax=d(item_data.get('tax', 0))
            )
            
            db.session.add(invoice_item)
            total += invoice_item.line_total
            
            # Create stock move
            stock_move = StockMove(
                project_id=project_id,
                warehouse_id=item_data['warehouse_id'],
                item_id=item_data['item_id'],
                qty_in=d(item_data['qty']),
                unit_cost=d(item_data['unit_cost']),
                amount=invoice_item.line_total,
                ref_type='PI',
                ref_id=invoice.id,
                move_date=invoice_date
            )
            
            db.session.add(stock_move)
        
        invoice.total = total
        db.session.commit()
        return invoice

class StockService:
    """Service for stock operations."""
    
    @staticmethod
    def issue_to_stage(project_id: str, warehouse_id: str, item_id: str, 
                      qty: Decimal, stage_id: str) -> Tuple[StockMove, Expense]:
        """Issue stock to stage and create expense."""
        item = Item.query.get(item_id)
        if not item:
            raise ValidationError("الصنف غير موجود")
        
        # Create stock move
        stock_move = StockMove(
            project_id=project_id,
            warehouse_id=warehouse_id,
            item_id=item_id,
            qty_out=qty,
            unit_cost=item.std_cost,
            amount=d(qty * item.std_cost),
            ref_type='ISSUE',
            ref_id=generate_uuid(),
            stage_id=stage_id,
            move_date=date.today()
        )
        
        db.session.add(stock_move)
        
        # Create expense
        expense = Expense(
            project_id=project_id,
            stage_id=stage_id,
            date=date.today(),
            amount=stock_move.amount,
            payee_type='other',
            description=f"إصدار مخزون: {item.name}"
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return stock_move, expense

class SettlementService:
    """Service for partner settlement operations."""
    
    @staticmethod
    def create_settlement_batch(project_id: str, cutoff_date: date, notes: str = None) -> PartnerSettleBatch:
        """Create settlement batch with preview."""
        # Calculate total project cost until cutoff
        total_cost = db.session.query(func.sum(Expense.amount)).filter(
            and_(Expense.project_id == project_id, Expense.date <= cutoff_date)
        ).scalar() or Decimal('0')
        
        # Add stock issues
        stock_cost = db.session.query(func.sum(StockMove.amount)).filter(
            and_(StockMove.project_id == project_id, 
                 StockMove.move_date <= cutoff_date,
                 StockMove.qty_out > 0)
        ).scalar() or Decimal('0')
        
        total_cost += stock_cost
        
        batch = PartnerSettleBatch(
            project_id=project_id,
            cutoff_date=cutoff_date,
            total_cost_until_cutoff=total_cost,
            notes=notes
        )
        
        db.session.add(batch)
        db.session.flush()
        
        # Create settlement lines
        project_partners = ProjectPartner.query.filter_by(project_id=project_id).all()
        
        for pp in project_partners:
            should_bear = d(total_cost * pp.share_pct / Decimal('100'))
            
            # Calculate actually paid (deposits - withdrawals + direct expenses)
            deposits = db.session.query(func.sum(Voucher.amount)).filter(
                and_(Voucher.project_id == project_id,
                     Voucher.party_id == pp.partner_id,
                     Voucher.v_type == 'receipt',
                     Voucher.v_date <= cutoff_date)
            ).scalar() or Decimal('0')
            
            withdrawals = db.session.query(func.sum(Voucher.amount)).filter(
                and_(Voucher.project_id == project_id,
                     Voucher.party_id == pp.partner_id,
                     Voucher.v_type == 'payment',
                     Voucher.v_date <= cutoff_date)
            ).scalar() or Decimal('0')
            
            direct_expenses = db.session.query(func.sum(Expense.amount)).filter(
                and_(Expense.project_id == project_id,
                     Expense.payee_type == 'partner',
                     Expense.payee_id == pp.partner_id,
                     Expense.date <= cutoff_date)
            ).scalar() or Decimal('0')
            
            actually_paid = deposits - withdrawals + direct_expenses
            diff = actually_paid - should_bear + pp.carry_forward_balance
            
            line = PartnerSettleLine(
                batch_id=batch.id,
                partner_id=pp.partner_id,
                share_pct_at_cutoff=pp.share_pct,
                should_bear_amount=should_bear,
                actually_paid_amount=actually_paid,
                diff_amount=diff
            )
            
            db.session.add(line)
        
        db.session.commit()
        return batch
    
    @staticmethod
    def post_settlement_batch(batch_id: str) -> PartnerSettleBatch:
        """Post settlement batch and update carry-forward balances."""
        batch = PartnerSettleBatch.query.get(batch_id)
        if not batch:
            raise ValidationError("دفعة التسوية غير موجودة")
        
        if batch.status != 'open':
            raise BusinessRuleError("دفعة التسوية غير مفتوحة")
        
        # Update carry-forward balances
        lines = PartnerSettleLine.query.filter_by(batch_id=batch_id).all()
        
        for line in lines:
            project_partner = ProjectPartner.query.filter_by(
                project_id=batch.project_id, partner_id=line.partner_id
            ).first()
            if project_partner:
                project_partner.carry_forward_balance += line.diff_amount
        
        # Update batch status
        batch.status = 'posted'
        batch.posted_at = datetime.utcnow()
        
        db.session.commit()
        return batch