"""SQLAlchemy Models"""
from db import db, TimestampMixin
from utils import generate_uuid, d
from decimal import Decimal
import json

# Core Models
class Project(db.Model, TimestampMixin):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    base_currency = db.Column(db.String(10), default='EGP', nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)
    
    # Relationships
    partners = db.relationship('ProjectPartner', back_populates='project', cascade='all, delete-orphan')
    warehouses = db.relationship('Warehouse', back_populates='project', cascade='all, delete-orphan')
    stages = db.relationship('Stage', back_populates='project', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', back_populates='project', cascade='all, delete-orphan')
    invoices = db.relationship('PurchaseInvoice', back_populates='project', cascade='all, delete-orphan')
    stock_moves = db.relationship('StockMove', back_populates='project', cascade='all, delete-orphan')
    vouchers = db.relationship('Voucher', back_populates='project', cascade='all, delete-orphan')
    allocations = db.relationship('Allocation', back_populates='project', cascade='all, delete-orphan')
    settlement_batches = db.relationship('PartnerSettleBatch', back_populates='project', cascade='all, delete-orphan')

class Partner(db.Model, TimestampMixin):
    __tablename__ = 'partners'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    projects = db.relationship('ProjectPartner', back_populates='partner', cascade='all, delete-orphan')
    vouchers = db.relationship('Voucher', foreign_keys='Voucher.party_id', 
                              primaryjoin="and_(Voucher.party_type=='partner', Voucher.party_id==Partner.id)")
    expenses = db.relationship('Expense', foreign_keys='Expense.payee_id',
                              primaryjoin="and_(Expense.payee_type=='partner', Expense.payee_id==Partner.id)")
    settlement_lines = db.relationship('PartnerSettleLine', back_populates='partner')
    claims_from = db.relationship('PartnerClaim', foreign_keys='PartnerClaim.from_partner_id', back_populates='from_partner')
    claims_to = db.relationship('PartnerClaim', foreign_keys='PartnerClaim.to_partner_id', back_populates='to_partner')

class ProjectPartner(db.Model, TimestampMixin):
    __tablename__ = 'project_partners'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    share_pct = db.Column(db.Numeric(5, 2), nullable=False)
    wallet_balance = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    carry_forward_balance = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    
    # Relationships
    project = db.relationship('Project', back_populates='partners')
    partner = db.relationship('Partner', back_populates='projects')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('project_id', 'partner_id'),
        db.CheckConstraint('share_pct >= 0 AND share_pct <= 100'),
    )

class Supplier(db.Model, TimestampMixin):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    invoices = db.relationship('PurchaseInvoice', back_populates='supplier')
    vouchers = db.relationship('Voucher', foreign_keys='Voucher.party_id',
                              primaryjoin="and_(Voucher.party_type=='supplier', Voucher.party_id==Supplier.id)",
                              overlaps="vouchers")
    expenses = db.relationship('Expense', foreign_keys='Expense.payee_id',
                              primaryjoin="and_(Expense.payee_type=='supplier', Expense.payee_id==Supplier.id)",
                              overlaps="expenses")

class Item(db.Model, TimestampMixin):
    __tablename__ = 'items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    uom = db.Column(db.String(20), default='unit', nullable=False)
    std_cost = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    
    # Relationships
    invoice_items = db.relationship('PurchaseInvoiceItem', back_populates='item')
    stock_moves = db.relationship('StockMove', back_populates='item')

class Warehouse(db.Model, TimestampMixin):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    project = db.relationship('Project', back_populates='warehouses')
    stock_moves = db.relationship('StockMove', back_populates='warehouse')

class Stage(db.Model, TimestampMixin):
    __tablename__ = 'stages'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    budget = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)
    
    # Relationships
    project = db.relationship('Project', back_populates='stages')
    expenses = db.relationship('Expense', back_populates='stage')
    stock_moves = db.relationship('StockMove', back_populates='stage')
    allocations = db.relationship('Allocation', back_populates='stage')

# Purchases & Stock
class PurchaseInvoice(db.Model, TimestampMixin):
    __tablename__ = 'purchase_invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    status = db.Column(db.String(20), default='posted', nullable=False)
    
    # Relationships
    project = db.relationship('Project', back_populates='invoices')
    supplier = db.relationship('Supplier', back_populates='invoices')
    items = db.relationship('PurchaseInvoiceItem', back_populates='invoice', cascade='all, delete-orphan')

class PurchaseInvoiceItem(db.Model, TimestampMixin):
    __tablename__ = 'purchase_invoice_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    invoice_id = db.Column(db.String(36), db.ForeignKey('purchase_invoices.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    qty = db.Column(db.Numeric(14, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), nullable=False)
    tax = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    
    # Relationships
    invoice = db.relationship('PurchaseInvoice', back_populates='items')
    item = db.relationship('Item', back_populates='invoice_items')

class StockMove(db.Model, TimestampMixin):
    __tablename__ = 'stock_moves'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    qty_in = db.Column(db.Numeric(14, 3), default=Decimal('0'), nullable=False)
    qty_out = db.Column(db.Numeric(14, 3), default=Decimal('0'), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), default=Decimal('0'), nullable=False)
    amount = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    ref_type = db.Column(db.String(20), nullable=True)  # 'PI' or 'ISSUE'
    ref_id = db.Column(db.String(36), nullable=True)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=True)
    move_date = db.Column(db.Date, nullable=False)
    
    # Relationships
    project = db.relationship('Project', back_populates='stock_moves')
    warehouse = db.relationship('Warehouse', back_populates='stock_moves')
    item = db.relationship('Item', back_populates='stock_moves')
    stage = db.relationship('Stage', back_populates='stock_moves')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_stock_move_date', 'move_date'),
        db.Index('idx_stock_move_project', 'project_id'),
    )

# Expenses & Wallet
class Expense(db.Model, TimestampMixin):
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payee_type = db.Column(db.String(20), nullable=False)  # 'supplier', 'partner', 'other'
    payee_id = db.Column(db.String(36), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    project = db.relationship('Project', back_populates='expenses')
    stage = db.relationship('Stage', back_populates='expenses')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_expense_date', 'date'),
        db.Index('idx_expense_project_stage', 'project_id', 'stage_id'),
    )

class Voucher(db.Model, TimestampMixin):
    __tablename__ = 'vouchers'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    v_type = db.Column(db.String(20), nullable=False)  # 'receipt' or 'payment'
    party_type = db.Column(db.String(20), nullable=False)  # 'partner', 'supplier', 'other'
    party_id = db.Column(db.String(36), nullable=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    v_date = db.Column(db.Date, nullable=False)
    ref_code = db.Column(db.String(50), unique=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    project = db.relationship('Project', back_populates='vouchers')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_voucher_date', 'v_date'),
        db.Index('idx_voucher_project', 'project_id'),
    )

# Allocation
class Allocation(db.Model, TimestampMixin):
    __tablename__ = 'allocations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=False)
    rule = db.Column(db.String(20), nullable=False)  # 'by_share' or 'custom'
    details_json = db.Column(db.Text, nullable=False)  # JSON: {partner_id: amount}
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    posted = db.Column(db.Boolean, default=False, nullable=False)
    alloc_date = db.Column(db.Date, nullable=False)
    
    # Relationships
    project = db.relationship('Project', back_populates='allocations')
    stage = db.relationship('Stage', back_populates='allocations')
    
    @property
    def details(self):
        """Parse details JSON"""
        return json.loads(self.details_json) if self.details_json else {}
    
    @details.setter
    def details(self, value):
        """Set details JSON"""
        self.details_json = json.dumps(value)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_allocation_date', 'alloc_date'),
        db.Index('idx_allocation_stage', 'stage_id'),
    )

# Settlements
class PartnerSettleBatch(db.Model, TimestampMixin):
    __tablename__ = 'partner_settle_batches'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    cutoff_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)  # 'open', 'posted', 'reversed'
    total_cost_until_cutoff = db.Column(db.Numeric(14, 2), default=Decimal('0'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    posted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    project = db.relationship('Project', back_populates='settlement_batches')
    lines = db.relationship('PartnerSettleLine', back_populates='batch', cascade='all, delete-orphan')
    claims = db.relationship('PartnerClaim', back_populates='batch', cascade='all, delete-orphan')

class PartnerSettleLine(db.Model, TimestampMixin):
    __tablename__ = 'partner_settle_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    batch_id = db.Column(db.String(36), db.ForeignKey('partner_settle_batches.id'), nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    share_pct_at_cutoff = db.Column(db.Numeric(5, 2), nullable=False)
    should_bear_amount = db.Column(db.Numeric(14, 2), nullable=False)
    actually_paid_amount = db.Column(db.Numeric(14, 2), nullable=False)
    diff_amount = db.Column(db.Numeric(14, 2), nullable=False)
    
    # Relationships
    batch = db.relationship('PartnerSettleBatch', back_populates='lines')
    partner = db.relationship('Partner', back_populates='settlement_lines')

class PartnerClaim(db.Model, TimestampMixin):
    __tablename__ = 'partner_claims'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    batch_id = db.Column(db.String(36), db.ForeignKey('partner_settle_batches.id'), nullable=False)
    from_partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    to_partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'settled', 'void'
    settled_voucher_id = db.Column(db.String(36), db.ForeignKey('vouchers.id'), nullable=True)
    settled_date = db.Column(db.Date, nullable=True)
    
    # Relationships
    batch = db.relationship('PartnerSettleBatch', back_populates='claims')
    from_partner = db.relationship('Partner', foreign_keys=[from_partner_id], back_populates='claims_from')
    to_partner = db.relationship('Partner', foreign_keys=[to_partner_id], back_populates='claims_to')