#!/usr/bin/env python3
"""
Musharaka Pro - Project Finance Management System
Flask backend with SQLAlchemy for managing projects, partners, and financial settlements.
"""

import os
import uuid
import json
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, CheckConstraint, UniqueConstraint
from dateutil.parser import parse as parse_date

# Initialize Flask app
app = Flask(__name__)

# Database configuration - Force SQLite for now
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///musharaka.db')

# Force SQLite to avoid PostgreSQL issues
if 'postgres' in DATABASE_URL.lower():
    DATABASE_URL = 'sqlite:///musharaka.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Decimal precision helpers
def quantize_decimal(value: Decimal) -> Decimal:
    """Quantize decimal to 2 decimal places for monetary values."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def quantize_percentage(value: Decimal) -> Decimal:
    """Quantize decimal to 2 decimal places for percentages."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# Response helpers
def ok_response(data: Any = None) -> Dict[str, Any]:
    """Create success response."""
    return {"ok": True, "data": data}

def error_response(error_code: str, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create error response."""
    response = {"ok": False, "error_code": error_code, "message": message}
    if details:
        response["details"] = details
    return response

# Base mixin for timestamps
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Core Models
class Project(db.Model, TimestampMixin):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    base_currency = db.Column(db.String(3), default='EGP', nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='open', nullable=False)
    
    # Relationships
    partners = db.relationship('ProjectPartner', backref='project', cascade='all, delete-orphan')
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
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    project_partners = db.relationship('ProjectPartner', backref='partner', cascade='all, delete-orphan')

class ProjectPartner(db.Model, TimestampMixin):
    __tablename__ = 'project_partners'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    share_pct = db.Column(db.Numeric(5, 2), nullable=False)
    wallet_balance = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    carry_forward_balance = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('project_id', 'partner_id', name='uq_project_partner'),
        CheckConstraint('share_pct >= 0 AND share_pct <= 100', name='ck_share_pct_range'),
    )
    
    # Relationships will be added later when needed

class Supplier(db.Model, TimestampMixin):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    purchase_invoices = db.relationship('PurchaseInvoice', backref='supplier', cascade='all, delete-orphan')

class Item(db.Model, TimestampMixin):
    __tablename__ = 'items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    uom = db.Column(db.String(20), default='unit', nullable=False)
    std_cost = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    
    # Relationships
    purchase_invoice_items = db.relationship('PurchaseInvoiceItem', backref='item', cascade='all, delete-orphan')
    stock_moves = db.relationship('StockMove', backref='item', cascade='all, delete-orphan')

class Warehouse(db.Model, TimestampMixin):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    
    # Relationships
    stock_moves = db.relationship('StockMove', backref='warehouse', cascade='all, delete-orphan')

class Stage(db.Model, TimestampMixin):
    __tablename__ = 'stages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    budget = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)
    
    # Relationships
    purchase_invoice_items = db.relationship('PurchaseInvoiceItem', backref='stage', cascade='all, delete-orphan')
    stock_moves = db.relationship('StockMove', backref='stage', cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='stage', cascade='all, delete-orphan')
    allocations = db.relationship('Allocation', backref='stage', cascade='all, delete-orphan')

# Purchase and Stock Models
class PurchaseInvoice(db.Model, TimestampMixin):
    __tablename__ = 'purchase_invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    total = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    status = db.Column(db.String(20), default='posted', nullable=False)
    
    # Relationships
    items = db.relationship('PurchaseInvoiceItem', backref='invoice', cascade='all, delete-orphan')

class PurchaseInvoiceItem(db.Model, TimestampMixin):
    __tablename__ = 'purchase_invoice_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey('purchase_invoices.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    qty = db.Column(db.Numeric(14, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), nullable=False)
    tax = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'))

class StockMove(db.Model, TimestampMixin):
    __tablename__ = 'stock_moves'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    qty_in = db.Column(db.Numeric(14, 3), default=0, nullable=False)
    qty_out = db.Column(db.Numeric(14, 3), default=0, nullable=False)
    unit_cost = db.Column(db.Numeric(14, 4), default=0, nullable=False)
    amount = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    ref_type = db.Column(db.String(10), nullable=False)  # 'PI' or 'ISSUE'
    ref_id = db.Column(db.String(36), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'))
    move_date = db.Column(db.Date, default=date.today, nullable=False)

# Expense and Wallet Models
class Expense(db.Model, TimestampMixin):
    __tablename__ = 'expenses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'))
    date = db.Column(db.Date, default=date.today, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payee_type = db.Column(db.String(20), nullable=False)  # 'supplier', 'partner', 'other'
    payee_id = db.Column(db.String(36))
    description = db.Column(db.Text)

class Voucher(db.Model, TimestampMixin):
    __tablename__ = 'vouchers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    v_type = db.Column(db.String(10), nullable=False)  # 'receipt' or 'payment'
    party_type = db.Column(db.String(20), nullable=False)  # 'partner', 'supplier', 'other'
    party_id = db.Column(db.String(36))
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    v_date = db.Column(db.Date, default=date.today, nullable=False)
    ref_code = db.Column(db.String(100), unique=True, nullable=False)
    notes = db.Column(db.Text)

# Allocation Models
class Allocation(db.Model, TimestampMixin):
    __tablename__ = 'allocations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    stage_id = db.Column(db.String(36), db.ForeignKey('stages.id'), nullable=False)
    rule = db.Column(db.String(20), nullable=False)  # 'by_share' or 'custom'
    details_json = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    posted = db.Column(db.Boolean, default=False, nullable=False)
    alloc_date = db.Column(db.Date, default=date.today, nullable=False)

# Settlement Models
class PartnerSettleBatch(db.Model, TimestampMixin):
    __tablename__ = 'partner_settle_batches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    cutoff_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)  # 'open', 'posted', 'reversed'
    total_cost_until_cutoff = db.Column(db.Numeric(14, 2), nullable=False)
    notes = db.Column(db.Text)
    posted_at = db.Column(db.DateTime)
    
    # Relationships
    lines = db.relationship('PartnerSettleLine', backref='batch', cascade='all, delete-orphan')
    claims = db.relationship('PartnerClaim', backref='batch', cascade='all, delete-orphan')

class PartnerSettleLine(db.Model, TimestampMixin):
    __tablename__ = 'partner_settle_lines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = db.Column(db.String(36), db.ForeignKey('partner_settle_batches.id'), nullable=False)
    partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    share_pct_at_cutoff = db.Column(db.Numeric(5, 2), nullable=False)
    should_bear_amount = db.Column(db.Numeric(14, 2), nullable=False)
    actually_paid_amount = db.Column(db.Numeric(14, 2), nullable=False)
    diff_amount = db.Column(db.Numeric(14, 2), nullable=False)
    
    # Relationships
    partner = db.relationship('Partner', backref='settlement_lines')

class PartnerClaim(db.Model, TimestampMixin):
    __tablename__ = 'partner_claims'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = db.Column(db.String(36), db.ForeignKey('partner_settle_batches.id'), nullable=False)
    from_partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    to_partner_id = db.Column(db.String(36), db.ForeignKey('partners.id'), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'settled', 'void'
    settled_voucher_id = db.Column(db.String(36))
    settled_date = db.Column(db.Date)

# Create indexes
Index('idx_project_partner_project', ProjectPartner.project_id)
Index('idx_project_partner_partner', ProjectPartner.partner_id)
Index('idx_stock_move_project', StockMove.project_id)
Index('idx_stock_move_date', StockMove.move_date)
Index('idx_expense_project', Expense.project_id)
Index('idx_expense_date', Expense.date)
Index('idx_voucher_ref_code', Voucher.ref_code)
Index('idx_allocation_stage', Allocation.stage_id)
Index('idx_settle_batch_project', PartnerSettleBatch.project_id)

# Business Logic Functions
def validate_share_totals(project_id: str) -> bool:
    """Validate that partner shares total 100% for a project."""
    total = db.session.query(db.func.sum(ProjectPartner.share_pct)).filter_by(project_id=project_id).scalar()
    return total == 100

def generate_voucher_ref_code(project_id: str, v_type: str) -> str:
    """Generate unique voucher reference code."""
    project_prefix = project_id[:8]
    year = datetime.now().year
    uuid_suffix = str(uuid.uuid4())[:6]
    prefix = 'RV' if v_type == 'receipt' else 'PV'
    return f"{prefix}-{project_prefix}-{year}-{uuid_suffix}"

def calculate_stage_cost(stage_id: str) -> Dict[str, Decimal]:
    """Calculate total cost for a stage including expenses and material costs."""
    # Sum of expenses for this stage
    expenses_total = db.session.query(db.func.sum(Expense.amount)).filter_by(stage_id=stage_id).scalar() or Decimal('0')
    
    # Sum of stock moves (material costs) for this stage
    materials_total = db.session.query(db.func.sum(StockMove.amount)).filter(
        StockMove.stage_id == stage_id,
        StockMove.qty_out > 0
    ).scalar() or Decimal('0')
    
    total_cost = expenses_total + materials_total
    
    return {
        'expenses': quantize_decimal(expenses_total),
        'materials': quantize_decimal(materials_total),
        'total': quantize_decimal(total_cost)
    }

def calculate_stage_allocation_delta(stage_id: str) -> Decimal:
    """Calculate allocation delta for a stage."""
    stage_cost = calculate_stage_cost(stage_id)
    total_cost = stage_cost['total']
    
    # Sum of already allocated amounts
    already_allocated = db.session.query(db.func.sum(Allocation.total_amount)).filter(
        Allocation.stage_id == stage_id,
        Allocation.posted == True
    ).scalar() or Decimal('0')
    
    delta = total_cost - already_allocated
    return quantize_decimal(delta)

def calculate_partner_balances(project_id: str, cutoff_date: date) -> Dict[str, Dict[str, Decimal]]:
    """Calculate partner balances for settlement."""
    partners = db.session.query(ProjectPartner).filter_by(project_id=project_id).all()
    results = {}
    
    # Calculate total project cost until cutoff
    total_cost = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.project_id == project_id,
        Expense.date <= cutoff_date
    ).scalar() or Decimal('0')
    
    # Add stock move costs
    stock_cost = db.session.query(db.func.sum(StockMove.amount)).filter(
        StockMove.project_id == project_id,
        StockMove.move_date <= cutoff_date,
        StockMove.qty_out > 0
    ).scalar() or Decimal('0')
    
    total_project_cost = total_cost + stock_cost
    
    for partner_link in partners:
        partner_id = partner_link.partner_id
        
        # Calculate should bear amount
        should_bear = quantize_decimal(total_project_cost * partner_link.share_pct / 100)
        
        # Calculate actually paid amount
        # Deposits (receipts)
        deposits = db.session.query(db.func.sum(Voucher.amount)).filter(
            Voucher.project_id == project_id,
            Voucher.party_type == 'partner',
            Voucher.party_id == partner_id,
            Voucher.v_type == 'receipt',
            Voucher.v_date <= cutoff_date
        ).scalar() or Decimal('0')
        
        # Withdrawals (payments)
        withdrawals = db.session.query(db.func.sum(Voucher.amount)).filter(
            Voucher.project_id == project_id,
            Voucher.party_type == 'partner',
            Voucher.party_id == partner_id,
            Voucher.v_type == 'payment',
            Voucher.v_date <= cutoff_date
        ).scalar() or Decimal('0')
        
        # Direct partner expenses
        direct_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.project_id == project_id,
            Expense.payee_type == 'partner',
            Expense.payee_id == partner_id,
            Expense.date <= cutoff_date
        ).scalar() or Decimal('0')
        
        actually_paid = deposits - withdrawals + direct_expenses
        
        # Calculate difference including carry forward
        diff = actually_paid - should_bear + partner_link.carry_forward_balance
        
        results[partner_id] = {
            'should_bear': should_bear,
            'actually_paid': quantize_decimal(actually_paid),
            'diff': quantize_decimal(diff),
            'share_pct': partner_link.share_pct,
            'carry_forward': partner_link.carry_forward_balance
        }
    
    return results

# API Routes
@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify(ok_response({
        'name': 'Musharaka Pro (no auth)',
        'version': 1
    }))

# Project endpoints
@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    data = request.get_json()
    
    if not data or 'code' not in data or 'name' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: code, name')), 400
    
    # Check if code already exists
    existing = Project.query.filter_by(code=data['code']).first()
    if existing:
        return jsonify(error_response('DUPLICATE_CODE', 'Project code already exists')), 400
    
    project = Project(
        code=data['code'],
        name=data['name'],
        base_currency=data.get('base_currency', 'EGP'),
        start_date=parse_date(data['start_date']).date() if data.get('start_date') else None,
        end_date=parse_date(data['end_date']).date() if data.get('end_date') else None
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': project.id,
        'code': project.code,
        'name': project.name,
        'base_currency': project.base_currency,
        'start_date': project.start_date.isoformat() if project.start_date else None,
        'end_date': project.end_date.isoformat() if project.end_date else None,
        'status': project.status
    })), 201

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all projects."""
    projects = Project.query.all()
    return jsonify(ok_response([{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'base_currency': p.base_currency,
        'start_date': p.start_date.isoformat() if p.start_date else None,
        'end_date': p.end_date.isoformat() if p.end_date else None,
        'status': p.status,
        'created_at': p.created_at.isoformat()
    } for p in projects]))

# Partner endpoints
@app.route('/api/partners', methods=['POST'])
def create_partner():
    """Create a new partner."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: name')), 400
    
    partner = Partner(name=data['name'])
    db.session.add(partner)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': partner.id,
        'name': partner.name
    })), 201

@app.route('/api/projects/<project_id>/partners', methods=['POST'])
def add_partner_to_project():
    """Add a partner to a project with share percentage."""
    project_id = request.view_args['project_id']
    data = request.get_json()
    
    if not data or 'partner_id' not in data or 'share_pct' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: partner_id, share_pct')), 400
    
    # Validate project exists
    project = Project.query.get(project_id)
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    # Validate partner exists
    partner = Partner.query.get(data['partner_id'])
    if not partner:
        return jsonify(error_response('NOT_FOUND', 'Partner not found')), 404
    
    # Check if partner already in project
    existing = ProjectPartner.query.filter_by(project_id=project_id, partner_id=data['partner_id']).first()
    if existing:
        return jsonify(error_response('DUPLICATE_PARTNER', 'Partner already in project')), 400
    
    share_pct = quantize_percentage(Decimal(str(data['share_pct'])))
    if share_pct < 0 or share_pct > 100:
        return jsonify(error_response('INVALID_SHARE', 'Share percentage must be between 0 and 100')), 400
    
    # Create project partner link
    project_partner = ProjectPartner(
        project_id=project_id,
        partner_id=data['partner_id'],
        share_pct=share_pct
    )
    
    db.session.add(project_partner)
    
    # Validate total shares
    if not validate_share_totals(project_id):
        db.session.rollback()
        return jsonify(error_response('SHARE_TOTAL', 'Partner shares must total exactly 100%')), 400
    
    db.session.commit()
    
    return jsonify(ok_response({
        'id': project_partner.id,
        'project_id': project_partner.project_id,
        'partner_id': project_partner.partner_id,
        'share_pct': float(project_partner.share_pct),
        'wallet_balance': float(project_partner.wallet_balance),
        'carry_forward_balance': float(project_partner.carry_forward_balance)
    })), 201

# Wallet endpoints
@app.route('/api/projects/<project_id>/partners/<partner_id>/wallet/deposit', methods=['POST'])
def deposit_to_wallet():
    """Deposit money to partner wallet."""
    project_id = request.view_args['project_id']
    partner_id = request.view_args['partner_id']
    data = request.get_json()
    
    if not data or 'amount' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: amount')), 400
    
    # Validate project partner exists
    project_partner = ProjectPartner.query.filter_by(project_id=project_id, partner_id=partner_id).first()
    if not project_partner:
        return jsonify(error_response('NOT_FOUND', 'Project partner not found')), 404
    
    amount = quantize_decimal(Decimal(str(data['amount'])))
    if amount <= 0:
        return jsonify(error_response('INVALID_AMOUNT', 'Amount must be positive')), 400
    
    # Create voucher
    voucher = Voucher(
        project_id=project_id,
        v_type='receipt',
        party_type='partner',
        party_id=partner_id,
        amount=amount,
        v_date=parse_date(data['date']).date() if data.get('date') else date.today(),
        ref_code=generate_voucher_ref_code(project_id, 'receipt'),
        notes=data.get('notes')
    )
    
    # Update wallet balance
    project_partner.wallet_balance += amount
    
    db.session.add(voucher)
    db.session.commit()
    
    return jsonify(ok_response({
        'voucher_id': voucher.id,
        'ref_code': voucher.ref_code,
        'amount': float(amount),
        'new_balance': float(project_partner.wallet_balance)
    })), 201

@app.route('/api/projects/<project_id>/partners/<partner_id>/wallet/withdraw', methods=['POST'])
def withdraw_from_wallet():
    """Withdraw money from partner wallet."""
    project_id = request.view_args['project_id']
    partner_id = request.view_args['partner_id']
    data = request.get_json()
    
    if not data or 'amount' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: amount')), 400
    
    # Validate project partner exists
    project_partner = ProjectPartner.query.filter_by(project_id=project_id, partner_id=partner_id).first()
    if not project_partner:
        return jsonify(error_response('NOT_FOUND', 'Project partner not found')), 404
    
    amount = quantize_decimal(Decimal(str(data['amount'])))
    if amount <= 0:
        return jsonify(error_response('INVALID_AMOUNT', 'Amount must be positive')), 400
    
    # Check sufficient balance
    if project_partner.wallet_balance < amount:
        return jsonify(error_response('INSUFFICIENT_FUNDS', 'Insufficient wallet balance')), 400
    
    # Create voucher
    voucher = Voucher(
        project_id=project_id,
        v_type='payment',
        party_type='partner',
        party_id=partner_id,
        amount=amount,
        v_date=parse_date(data['date']).date() if data.get('date') else date.today(),
        ref_code=generate_voucher_ref_code(project_id, 'payment'),
        notes=data.get('notes')
    )
    
    # Update wallet balance
    project_partner.wallet_balance -= amount
    
    db.session.add(voucher)
    db.session.commit()
    
    return jsonify(ok_response({
        'voucher_id': voucher.id,
        'ref_code': voucher.ref_code,
        'amount': float(amount),
        'new_balance': float(project_partner.wallet_balance)
    })), 201

# Additional API Routes (moved from routes.py to avoid circular imports)

# Supplier endpoints
@app.route('/api/suppliers', methods=['POST'])
def create_supplier():
    """Create a new supplier."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: name')), 400
    
    supplier = Supplier(name=data['name'])
    db.session.add(supplier)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': supplier.id,
        'name': supplier.name
    })), 201

# Item endpoints
@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item."""
    data = request.get_json()
    
    if not data or 'sku' not in data or 'name' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: sku, name')), 400
    
    # Check if SKU already exists
    existing = Item.query.filter_by(sku=data['sku']).first()
    if existing:
        return jsonify(error_response('DUPLICATE_SKU', 'Item SKU already exists')), 400
    
    item = Item(
        sku=data['sku'],
        name=data['name'],
        uom=data.get('uom', 'unit'),
        std_cost=quantize_decimal(Decimal(str(data.get('std_cost', 0))))
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': item.id,
        'sku': item.sku,
        'name': item.name,
        'uom': item.uom,
        'std_cost': float(item.std_cost)
    })), 201

# Warehouse endpoints
@app.route('/api/projects/<project_id>/warehouses', methods=['POST'])
def create_warehouse():
    """Create a new warehouse for a project."""
    project_id = request.view_args['project_id']
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: name')), 400
    
    # Validate project exists
    project = Project.query.get(project_id)
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    warehouse = Warehouse(
        project_id=project_id,
        name=data['name']
    )
    
    db.session.add(warehouse)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': warehouse.id,
        'project_id': warehouse.project_id,
        'name': warehouse.name
    })), 201

# Stage endpoints
@app.route('/api/projects/<project_id>/stages', methods=['POST'])
def create_stage():
    """Create a new stage for a project."""
    project_id = request.view_args['project_id']
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: name')), 400
    
    # Validate project exists
    project = Project.query.get(project_id)
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    stage = Stage(
        project_id=project_id,
        name=data['name'],
        budget=quantize_decimal(Decimal(str(data.get('budget', 0))))
    )
    
    db.session.add(stage)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': stage.id,
        'project_id': stage.project_id,
        'name': stage.name,
        'budget': float(stage.budget),
        'status': stage.status
    })), 201

# Expense endpoints
@app.route('/api/expenses', methods=['POST'])
def create_expense():
    """Create a new expense."""
    data = request.get_json()
    
    if not data or 'project_id' not in data or 'amount' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: project_id, amount')), 400
    
    # Validate project exists
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    # Validate stage if provided
    if data.get('stage_id'):
        stage = Stage.query.get(data['stage_id'])
        if not stage:
            return jsonify(error_response('NOT_FOUND', 'Stage not found')), 404
    
    amount = quantize_decimal(Decimal(str(data['amount'])))
    if amount <= 0:
        return jsonify(error_response('INVALID_AMOUNT', 'Amount must be positive')), 400
    
    expense = Expense(
        project_id=data['project_id'],
        stage_id=data.get('stage_id'),
        date=parse_date(data['date']).date() if data.get('date') else date.today(),
        amount=amount,
        payee_type=data.get('payee_type', 'other'),
        payee_id=data.get('payee_id'),
        description=data.get('description')
    )
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify(ok_response({
        'id': expense.id,
        'project_id': expense.project_id,
        'stage_id': expense.stage_id,
        'amount': float(expense.amount),
        'date': expense.date.isoformat(),
        'payee_type': expense.payee_type,
        'payee_id': expense.payee_id,
        'description': expense.description
    })), 201

# Stage cost endpoint
@app.route('/api/stages/<stage_id>/cost', methods=['GET'])
def get_stage_cost():
    """Get stage cost breakdown."""
    stage_id = request.view_args['stage_id']
    
    # Validate stage exists
    stage = Stage.query.get(stage_id)
    if not stage:
        return jsonify(error_response('NOT_FOUND', 'Stage not found')), 404
    
    cost_breakdown = calculate_stage_cost(stage_id)
    
    return jsonify(ok_response({
        'stage_id': stage_id,
        'stage_name': stage.name,
        'expenses': float(cost_breakdown['expenses']),
        'materials': float(cost_breakdown['materials']),
        'total': float(cost_breakdown['total'])
    }))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get port from environment variable (for Render)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)