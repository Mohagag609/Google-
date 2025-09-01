#!/usr/bin/env python3
"""
SQLAlchemy models for Musharaka Pro
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Index, CheckConstraint, UniqueConstraint
from db import db
from utils import generate_uuid, d

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Project(db.Model, TimestampMixin):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    base_currency = db.Column(db.String(3), default='EGP', nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)  # 'open', 'closed'
    
    # Relationships
    project_partners = db.relationship('ProjectPartner', backref='project', cascade='all, delete-orphan')
    warehouses = db.relationship('Warehouse', backref='project', cascade='all, delete-orphan')
    stages = db.relationship('Stage', backref='project', cascade='all, delete-orphan')
    purchase_invoices = db.relationship('PurchaseInvoice', backref='project', cascade='all, delete-orphan')
    stock_moves = db.relationship('StockMove', backref='project', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='project', cascade='all, delete-orphan')
    vouchers = db.relationship('Voucher', backref='project', cascade='all, delete-orphan')
    allocations = db.relationship('Allocation', backref='project', cascade='all, delete-orphan')
    settlement_batches = db.relationship('PartnerSettleBatch', backref='project', cascade='all, delete-orphan')

class Partner(db.Model, TimestampMixin):
    __tablename__ = 'partners'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    project_partners = db.relationship('ProjectPartner', backref='partner', cascade='all, delete-orphan')
    settlement_lines = db.relationship('PartnerSettleLine', backref='partner', cascade='all, delete-orphan')
    claims_as_debtor = db.relationship('PartnerClaim', foreign_keys='PartnerClaim.from_partner_id', backref='debtor_partner', cascade='all, delete-orphan')
    claims_as_creditor = db.relationship('PartnerClaim', foreign_keys='PartnerClaim.to_partner_id', backref='creditor_partner', cascade='all, delete-orphan')

class ProjectPartner(db.Model, TimestampMixin):
    __tablename__ = 'project_partners'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    share_pct = db.Column(db.Numeric(5, 2), nullable=False)
    wallet_balance = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    carry_forward_balance = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('project_id', 'partner_id', name='uq_project_partner'),
        CheckConstraint('share_pct >= 0 AND share_pct <= 100', name='ck_share_pct_range'),
    )

class Supplier(db.Model, TimestampMixin):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    purchase_invoices = db.relationship('PurchaseInvoice', backref='supplier', cascade='all, delete-orphan')

class Item(db.Model, TimestampMixin):
    __tablename__ = 'items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    uom = db.Column(db.String(20), default='unit', nullable=False)
    std_cost = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    
    # Relationships
    purchase_invoice_items = db.relationship('PurchaseInvoiceItem', backref='item', cascade='all, delete-orphan')
    stock_moves = db.relationship('StockMove', backref='item', cascade='all, delete-orphan')

class Warehouse(db.Model, TimestampMixin):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    stock_moves = db.relationship('StockMove', backref='warehouse', cascade='all, delete-orphan')

class Stage(db.Model, TimestampMixin):
    __tablename__ = 'stages'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    budget = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)  # 'open', 'closed'
    
    # Relationships
    stock_moves = db.relationship('StockMove', backref='stage', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='stage', cascade='all, delete-orphan')
    allocations = db.relationship('Allocation', backref='stage', cascade='all, delete-orphan')

class PurchaseInvoice(db.Model, TimestampMixin):
    __tablename__ = 'purchase_invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default='posted', nullable=False)  # 'draft', 'posted'
    
    # Relationships
    items = db.relationship('PurchaseInvoiceItem', backref='invoice', cascade='all, delete-orphan')

class PurchaseInvoiceItem(db.Model, TimestampMixin):
    __tablename__ = 'purchase_invoice_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    invoice_id = db.Column(db.String(36), db.ForeignKey('purchase_invoices.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    qty = db.Column(db.Numeric(14, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), nullable=False)
    tax = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    
    @property
    def line_total(self):
        return d(self.qty * self.unit_cost + self.tax)

class StockMove(db.Model, TimestampMixin):
    __tablename__ = 'stock_moves'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    qty_in = db.Column(db.Numeric(14, 3), default=0, nullable=False)
    qty_out = db.Column(db.Numeric(14, 3), default=0, nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), default=0, nullable=False)
    amount = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    ref_type = db.Column(db.String(10), nullable=False)  # 'PI', 'ISSUE'
    ref_id = db.Column(db.String(36), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=True)
    move_date = db.Column(db.Date, nullable=False)

class Expense(db.Model, TimestampMixin):
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payee_type = db.Column(db.String(20), nullable=False)  # 'supplier', 'partner', 'other'
    payee_id = db.Column(db.String(36), nullable=True)
    description = db.Column(db.Text, nullable=False)

class Voucher(db.Model, TimestampMixin):
    __tablename__ = 'vouchers'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    v_type = db.Column(db.String(20), nullable=False)  # 'receipt', 'payment'
    party_type = db.Column(db.String(20), nullable=False)  # 'partner', 'supplier', 'other'
    party_id = db.Column(db.String(36), nullable=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    v_date = db.Column(db.Date, nullable=False)
    ref_code = db.Column(db.String(50), unique=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)

class Allocation(db.Model, TimestampMixin):
    __tablename__ = 'allocations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=False)
    rule = db.Column(db.String(20), nullable=False)  # 'by_share', 'custom'
    details_json = db.Column(db.Text, nullable=True)  # JSON for custom allocations
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    posted = db.Column(db.Boolean, default=False, nullable=False)
    alloc_date = db.Column(db.Date, nullable=False)

class PartnerSettleBatch(db.Model, TimestampMixin):
    __tablename__ = 'partner_settle_batches'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    cutoff_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)  # 'open', 'posted', 'reversed'
    total_cost_until_cutoff = db.Column(db.Numeric(14, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    posted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    lines = db.relationship('PartnerSettleLine', backref='batch', cascade='all, delete-orphan')
    claims = db.relationship('PartnerClaim', backref='batch', cascade='all, delete-orphan')

class PartnerSettleLine(db.Model, TimestampMixin):
    __tablename__ = 'partner_settle_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    batch_id = db.Column(db.String(36), db.ForeignKey('partner_settle_batches.id'), nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    share_pct_at_cutoff = db.Column(db.Numeric(5, 2), nullable=False)
    should_bear_amount = db.Column(db.Numeric(14, 2), nullable=False)
    actually_paid_amount = db.Column(db.Numeric(14, 2), nullable=False)
    diff_amount = db.Column(db.Numeric(14, 2), nullable=False)

class PartnerClaim(db.Model, TimestampMixin):
    __tablename__ = 'partner_claims'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    batch_id = db.Column(db.String(36), db.ForeignKey('partner_settle_batches.id'), nullable=False)
    from_partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    to_partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'settled', 'void'
    settled_voucher_id = db.Column(db.String(36), nullable=True)
    settled_date = db.Column(db.Date, nullable=True)

# Create indexes
Index('idx_project_partner_project', ProjectPartner.project_id)
Index('idx_project_partner_partner', ProjectPartner.partner_id)
Index('idx_stock_move_project', StockMove.project_id)
Index('idx_stock_move_date', StockMove.move_date)
Index('idx_expense_project', Expense.project_id)
Index('idx_expense_date', Expense.date)
Index('idx_voucher_ref_code', Voucher.ref_code)
Index('idx_allocation_stage', Allocation.stage_id)