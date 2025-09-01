"""
Additional API routes for Musharaka Pro
"""

from flask import request, jsonify
from decimal import Decimal
from datetime import date, datetime
from dateutil.parser import parse as parse_date
import json
import uuid

# Import from the main app module
from app import (
    app, db, ok_response, error_response, quantize_decimal, quantize_percentage,
    Supplier, Item, Warehouse, Stage, PurchaseInvoice, PurchaseInvoiceItem, 
    StockMove, Expense, Voucher, Allocation, PartnerSettleBatch, PartnerSettleLine, 
    PartnerClaim, calculate_stage_cost, calculate_stage_allocation_delta,
    calculate_partner_balances, generate_voucher_ref_code, Project, ProjectPartner
)

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

# Purchase endpoints
@app.route('/api/purchases/invoices', methods=['POST'])
def create_purchase_invoice():
    """Create a purchase invoice with items."""
    data = request.get_json()
    
    if not data or 'project_id' not in data or 'supplier_id' not in data or 'warehouse_id' not in data or 'items' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: project_id, supplier_id, warehouse_id, items')), 400
    
    # Validate entities exist
    from app import Project
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    supplier = Supplier.query.get(data['supplier_id'])
    if not supplier:
        return jsonify(error_response('NOT_FOUND', 'Supplier not found')), 404
    
    warehouse = Warehouse.query.get(data['warehouse_id'])
    if not warehouse:
        return jsonify(error_response('NOT_FOUND', 'Warehouse not found')), 404
    
    # Create invoice
    invoice = PurchaseInvoice(
        project_id=data['project_id'],
        supplier_id=data['supplier_id'],
        date=parse_date(data['date']).date() if data.get('date') else date.today()
    )
    
    db.session.add(invoice)
    db.session.flush()  # Get the invoice ID
    
    total_amount = Decimal('0')
    
    # Create invoice items and stock moves
    for item_data in data['items']:
        if 'item_id' not in item_data or 'qty' not in item_data or 'unit_cost' not in item_data:
            db.session.rollback()
            return jsonify(error_response('INVALID_DATA', 'Missing required item fields: item_id, qty, unit_cost')), 400
        
        # Validate item exists
        item = Item.query.get(item_data['item_id'])
        if not item:
            db.session.rollback()
            return jsonify(error_response('NOT_FOUND', f'Item not found: {item_data["item_id"]}')), 404
        
        qty = Decimal(str(item_data['qty']))
        unit_cost = Decimal(str(item_data['unit_cost']))
        tax = Decimal(str(item_data.get('tax', 0)))
        
        # Create invoice item
        invoice_item = PurchaseInvoiceItem(
            invoice_id=invoice.id,
            item_id=item_data['item_id'],
            qty=qty,
            unit_cost=unit_cost,
            tax=tax,
            stage_id=item_data.get('stage_id')
        )
        
        db.session.add(invoice_item)
        
        # Create stock move
        amount = qty * unit_cost
        total_amount += amount
        
        stock_move = StockMove(
            project_id=data['project_id'],
            warehouse_id=data['warehouse_id'],
            item_id=item_data['item_id'],
            qty_in=qty,
            unit_cost=unit_cost,
            amount=quantize_decimal(amount),
            ref_type='PI',
            ref_id=invoice.id,
            stage_id=item_data.get('stage_id'),
            move_date=invoice.date
        )
        
        db.session.add(stock_move)
    
    # Update invoice total
    invoice.total = quantize_decimal(total_amount)
    
    db.session.commit()
    
    return jsonify(ok_response({
        'invoice_id': invoice.id,
        'total': float(invoice.total)
    })), 201

# Stock issue endpoint
@app.route('/api/stock/issue', methods=['POST'])
def issue_stock():
    """Issue stock to a stage."""
    data = request.get_json()
    
    if not data or 'project_id' not in data or 'warehouse_id' not in data or 'stage_id' not in data or 'item_id' not in data or 'qty' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: project_id, warehouse_id, stage_id, item_id, qty')), 400
    
    # Validate entities exist
    from app import Project
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    warehouse = Warehouse.query.get(data['warehouse_id'])
    if not warehouse:
        return jsonify(error_response('NOT_FOUND', 'Warehouse not found')), 404
    
    stage = Stage.query.get(data['stage_id'])
    if not stage:
        return jsonify(error_response('NOT_FOUND', 'Stage not found')), 404
    
    item = Item.query.get(data['item_id'])
    if not item:
        return jsonify(error_response('NOT_FOUND', 'Item not found')), 404
    
    qty = Decimal(str(data['qty']))
    if qty <= 0:
        return jsonify(error_response('INVALID_AMOUNT', 'Quantity must be positive')), 400
    
    # Create stock move
    amount = qty * item.std_cost
    stock_move = StockMove(
        project_id=data['project_id'],
        warehouse_id=data['warehouse_id'],
        item_id=data['item_id'],
        qty_out=qty,
        unit_cost=item.std_cost,
        amount=quantize_decimal(amount),
        ref_type='ISSUE',
        ref_id=str(uuid.uuid4()),  # Generate unique ref_id for stock issue
        stage_id=data['stage_id'],
        move_date=parse_date(data['date']).date() if data.get('date') else date.today()
    )
    
    db.session.add(stock_move)
    
    # Create expense for the stage
    expense = Expense(
        project_id=data['project_id'],
        stage_id=data['stage_id'],
        date=stock_move.move_date,
        amount=stock_move.amount,
        payee_type='other',
        description=f'Material cost for {item.name} (qty: {qty})'
    )
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify(ok_response({
        'stock_move_id': stock_move.id,
        'expense_id': expense.id,
        'amount': float(stock_move.amount)
    })), 201

# Expense endpoints
@app.route('/api/expenses', methods=['POST'])
def create_expense():
    """Create a new expense."""
    data = request.get_json()
    
    if not data or 'project_id' not in data or 'amount' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: project_id, amount')), 400
    
    # Validate project exists
    from app import Project
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

# Stage allocation endpoint
@app.route('/api/stages/<stage_id>/allocate', methods=['POST'])
def allocate_stage_cost():
    """Allocate stage cost to partners."""
    stage_id = request.view_args['stage_id']
    data = request.get_json()
    
    if not data or 'rule' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required field: rule')), 400
    
    # Validate stage exists
    stage = Stage.query.get(stage_id)
    if not stage:
        return jsonify(error_response('NOT_FOUND', 'Stage not found')), 404
    
    # Calculate delta
    delta = calculate_stage_allocation_delta(stage_id)
    if delta <= 0:
        return jsonify(error_response('NO_DELTA', 'No allocation delta available')), 400
    
    rule = data['rule']
    if rule not in ['by_share', 'custom']:
        return jsonify(error_response('INVALID_RULE', 'Rule must be by_share or custom')), 400
    
    # Get project partners
    project_partners = ProjectPartner.query.filter_by(project_id=stage.project_id).all()
    
    if not project_partners:
        return jsonify(error_response('NO_PARTNERS', 'No partners found for project')), 400
    
    # Calculate per-partner amounts
    per_partner = {}
    
    if rule == 'by_share':
        for partner_link in project_partners:
            amount = quantize_decimal(delta * partner_link.share_pct / 100)
            per_partner[partner_link.partner_id] = amount
    else:  # custom
        if 'details' not in data:
            return jsonify(error_response('INVALID_DATA', 'Missing required field: details for custom allocation')), 400
        
        details = data['details']
        custom_total = sum(Decimal(str(amount)) for amount in details.values())
        
        if custom_total != delta:
            return jsonify(error_response('BAD_CUSTOM', 'Custom allocation total must equal delta')), 400
        
        per_partner = {partner_id: quantize_decimal(Decimal(str(amount))) for partner_id, amount in details.items()}
    
    # Update partner wallets and create allocation
    for partner_link in project_partners:
        partner_id = partner_link.partner_id
        amount = per_partner.get(partner_id, Decimal('0'))
        
        if amount > 0:
            # Check sufficient balance
            if partner_link.wallet_balance < amount:
                db.session.rollback()
                return jsonify(error_response('INSUFFICIENT_FUNDS', f'Insufficient balance for partner {partner_id}')), 400
            
            # Deduct from wallet
            partner_link.wallet_balance -= amount
    
    # Create allocation record
    allocation = Allocation(
        project_id=stage.project_id,
        stage_id=stage_id,
        rule=rule,
        details_json=json.dumps({k: float(v) for k, v in per_partner.items()}),
        total_amount=delta,
        posted=True,
        alloc_date=date.today()
    )
    
    db.session.add(allocation)
    db.session.commit()
    
    return jsonify(ok_response({
        'allocation_id': allocation.id,
        'stage_id': stage_id,
        'rule': rule,
        'total_amount': float(delta),
        'per_partner': {k: float(v) for k, v in per_partner.items()}
    })), 201

# Settlement endpoints
@app.route('/api/settlements', methods=['POST'])
def create_settlement():
    """Create a settlement batch."""
    data = request.get_json()
    
    if not data or 'project_id' not in data or 'cutoff_date' not in data:
        return jsonify(error_response('INVALID_DATA', 'Missing required fields: project_id, cutoff_date')), 400
    
    # Validate project exists
    from app import Project
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify(error_response('NOT_FOUND', 'Project not found')), 404
    
    cutoff_date = parse_date(data['cutoff_date']).date()
    
    # Calculate partner balances
    partner_balances = calculate_partner_balances(data['project_id'], cutoff_date)
    
    # Calculate total project cost
    total_cost = sum(balance['should_bear'] for balance in partner_balances.values())
    
    # Create settlement batch
    batch = PartnerSettleBatch(
        project_id=data['project_id'],
        cutoff_date=cutoff_date,
        total_cost_until_cutoff=quantize_decimal(total_cost),
        notes=data.get('notes')
    )
    
    db.session.add(batch)
    db.session.flush()  # Get batch ID
    
    # Create settlement lines
    creditors = []
    debtors = []
    
    for partner_id, balance in partner_balances.items():
        line = PartnerSettleLine(
            batch_id=batch.id,
            partner_id=partner_id,
            share_pct_at_cutoff=balance['share_pct'],
            should_bear_amount=balance['should_bear'],
            actually_paid_amount=balance['actually_paid'],
            diff_amount=balance['diff']
        )
        
        db.session.add(line)
        
        # Categorize for claims
        if balance['diff'] > 0:
            creditors.append((partner_id, balance['diff']))
        elif balance['diff'] < 0:
            debtors.append((partner_id, abs(balance['diff'])))
    
    # Create claims using greedy matching
    claims = []
    for debtor_id, debtor_amount in debtors:
        remaining_debt = debtor_amount
        
        for creditor_id, creditor_amount in creditors:
            if remaining_debt <= 0:
                break
            
            if creditor_amount <= 0:
                continue
            
            # Create claim for the smaller of remaining debt or available credit
            claim_amount = min(remaining_debt, creditor_amount)
            
            claim = PartnerClaim(
                batch_id=batch.id,
                from_partner_id=debtor_id,
                to_partner_id=creditor_id,
                amount=quantize_decimal(claim_amount)
            )
            
            db.session.add(claim)
            claims.append(claim)
            
            remaining_debt -= claim_amount
            # Update creditor amount (simplified - in real implementation, track remaining)
            creditors = [(cid, camt - claim_amount if cid == creditor_id else camt) for cid, camt in creditors]
    
    db.session.commit()
    
    return jsonify(ok_response({
        'batch_id': batch.id,
        'project_id': data['project_id'],
        'cutoff_date': cutoff_date.isoformat(),
        'total_cost': float(total_cost),
        'status': batch.status,
        'lines_count': len(partner_balances),
        'claims_count': len(claims)
    })), 201

@app.route('/api/settlements/<batch_id>/post', methods=['POST'])
def post_settlement():
    """Post a settlement batch."""
    batch_id = request.view_args['batch_id']
    
    # Validate batch exists
    batch = PartnerSettleBatch.query.get(batch_id)
    if not batch:
        return jsonify(error_response('NOT_FOUND', 'Settlement batch not found')), 404
    
    if batch.status != 'open':
        return jsonify(error_response('INVALID_STATUS', 'Batch is not open for posting')), 400
    
    # Update carry forward balances
    for line in batch.lines:
        project_partner = ProjectPartner.query.filter_by(
            project_id=batch.project_id,
            partner_id=line.partner_id
        ).first()
        
        if project_partner:
            project_partner.carry_forward_balance += line.diff_amount
    
    # Update batch status
    batch.status = 'posted'
    batch.posted_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(ok_response({
        'batch_id': batch.id,
        'status': batch.status,
        'posted_at': batch.posted_at.isoformat()
    }))

@app.route('/api/settlements/<batch_id>', methods=['GET'])
def get_settlement():
    """Get settlement batch details."""
    batch_id = request.view_args['batch_id']
    
    # Validate batch exists
    batch = PartnerSettleBatch.query.get(batch_id)
    if not batch:
        return jsonify(error_response('NOT_FOUND', 'Settlement batch not found')), 404
    
    # Get lines
    lines = []
    for line in batch.lines:
        lines.append({
            'partner_id': line.partner_id,
            'share_pct': float(line.share_pct_at_cutoff),
            'should_bear': float(line.should_bear_amount),
            'actually_paid': float(line.actually_paid_amount),
            'diff': float(line.diff_amount)
        })
    
    # Get claims
    claims = []
    for claim in batch.claims:
        claims.append({
            'id': claim.id,
            'from_partner_id': claim.from_partner_id,
            'to_partner_id': claim.to_partner_id,
            'amount': float(claim.amount),
            'status': claim.status,
            'settled_voucher_id': claim.settled_voucher_id,
            'settled_date': claim.settled_date.isoformat() if claim.settled_date else None
        })
    
    return jsonify(ok_response({
        'batch_id': batch.id,
        'project_id': batch.project_id,
        'cutoff_date': batch.cutoff_date.isoformat(),
        'total_cost': float(batch.total_cost_until_cutoff),
        'status': batch.status,
        'notes': batch.notes,
        'posted_at': batch.posted_at.isoformat() if batch.posted_at else None,
        'lines': lines,
        'claims': claims
    }))

# Report endpoints
@app.route('/api/reports/partner-statement', methods=['GET'])
def get_partner_statement():
    """Get partner statement."""
    project_id = request.args.get('project_id')
    partner_id = request.args.get('partner_id')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    if not project_id or not partner_id:
        return jsonify(error_response('INVALID_DATA', 'Missing required parameters: project_id, partner_id')), 400
    
    # Validate project partner exists
    project_partner = ProjectPartner.query.filter_by(project_id=project_id, partner_id=partner_id).first()
    if not project_partner:
        return jsonify(error_response('NOT_FOUND', 'Project partner not found')), 404
    
    # Get movements
    movements = []
    
    # Get vouchers (deposits/withdrawals)
    vouchers_query = Voucher.query.filter(
        Voucher.project_id == project_id,
        Voucher.party_type == 'partner',
        Voucher.party_id == partner_id
    )
    
    if from_date:
        vouchers_query = vouchers_query.filter(Voucher.v_date >= parse_date(from_date).date())
    if to_date:
        vouchers_query = vouchers_query.filter(Voucher.v_date <= parse_date(to_date).date())
    
    for voucher in vouchers_query.order_by(Voucher.v_date):
        movements.append({
            'date': voucher.v_date.isoformat(),
            'type': 'deposit' if voucher.v_type == 'receipt' else 'withdrawal',
            'amount': float(voucher.amount),
            'ref_code': voucher.ref_code,
            'notes': voucher.notes
        })
    
    # Get allocations
    allocations_query = Allocation.query.join(Stage).filter(
        Stage.project_id == project_id,
        Allocation.posted == True
    )
    
    if from_date:
        allocations_query = allocations_query.filter(Allocation.alloc_date >= parse_date(from_date).date())
    if to_date:
        allocations_query = allocations_query.filter(Allocation.alloc_date <= parse_date(to_date).date())
    
    for allocation in allocations_query.order_by(Allocation.alloc_date):
        details = json.loads(allocation.details_json)
        if partner_id in details:
            movements.append({
                'date': allocation.alloc_date.isoformat(),
                'type': 'allocation',
                'amount': -float(details[partner_id]),  # Negative for allocation
                'stage_name': allocation.stage.name,
                'rule': allocation.rule
            })
    
    # Sort movements by date
    movements.sort(key=lambda x: x['date'])
    
    return jsonify(ok_response({
        'partner_id': partner_id,
        'project_id': project_id,
        'wallet_balance': float(project_partner.wallet_balance),
        'carry_forward_balance': float(project_partner.carry_forward_balance),
        'movements': movements
    }))