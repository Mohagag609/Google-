"""Main Flask application"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from db import init_db, db
from models import *
from utils import *
from services import wallets, allocations, settlements, purchases, stock, reports
from datetime import datetime, date
import os
from decimal import Decimal

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
init_db(app)

# Template filters
@app.template_filter('money')
def money_filter(value):
    return format_money(value)

@app.template_filter('date')
def date_filter(value):
    return format_date(value)

# Template globals
@app.context_processor
def utility_processor():
    return dict(now=datetime.now)

# Routes

# Dashboard
@app.route('/')
def index():
    """Dashboard with projects and partners"""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    partners = Partner.query.order_by(Partner.name).all()
    return render_template('index.html', projects=projects, partners=partners)

@app.route('/projects', methods=['POST'])
def create_project():
    """Create new project"""
    try:
        code = request.form.get('code')
        name = request.form.get('name')
        
        # Check if code exists
        if Project.query.filter_by(code=code).first():
            raise ValidationError("كود المشروع موجود بالفعل")
        
        project = Project(code=code, name=name)
        db.session.add(project)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/project_row.html', project=project)
        
        flash_success("تم إنشاء المشروع بنجاح")
        return redirect(url_for('index'))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('index'))

@app.route('/partners', methods=['POST'])
def create_partner():
    """Create new partner"""
    try:
        name = request.form.get('name')
        
        partner = Partner(name=name)
        db.session.add(partner)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/partner_option.html', partner=partner)
        
        flash_success("تم إضافة الشريك بنجاح")
        return redirect(url_for('index'))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('index'))

# Project Management
@app.route('/projects/<project_id>')
def project_home(project_id):
    """Project home page"""
    project = Project.query.get_or_404(project_id)
    project_partners = ProjectPartner.query.filter_by(project_id=project_id).all()
    all_partners = Partner.query.order_by(Partner.name).all()
    stages = Stage.query.filter_by(project_id=project_id).order_by(Stage.created_at).all()
    warehouses = Warehouse.query.filter_by(project_id=project_id).all()
    
    # Calculate total shares
    total_shares = sum(d(pp.share_pct) for pp in project_partners)
    
    # Get project summary
    summary = reports.get_project_summary(project_id)
    
    return render_template('projects/project_home.html',
                         project=project,
                         project_partners=project_partners,
                         all_partners=all_partners,
                         stages=stages,
                         warehouses=warehouses,
                         total_shares=total_shares,
                         summary=summary)

@app.route('/projects/<project_id>/partners/link', methods=['POST'])
def link_partner(project_id):
    """Link partner to project"""
    try:
        partner_id = request.form.get('partner_id')
        share_pct = d(request.form.get('share_pct'))
        
        # Check if already linked
        existing = ProjectPartner.query.filter_by(
            project_id=project_id,
            partner_id=partner_id
        ).first()
        
        if existing:
            raise ValidationError("الشريك مرتبط بالفعل بالمشروع")
        
        # Create link
        pp = ProjectPartner(
            project_id=project_id,
            partner_id=partner_id,
            share_pct=share_pct
        )
        db.session.add(pp)
        db.session.flush()
        
        # Validate total shares
        total_shares = db.session.query(
            db.func.sum(ProjectPartner.share_pct)
        ).filter_by(project_id=project_id).scalar()
        
        if d(total_shares) > Decimal("100.00"):
            db.session.rollback()
            raise ValidationError(f"مجموع الحصص تجاوز 100% ({d(total_shares)}%)")
        
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/partner_link_row.html', pp=pp)
        
        flash_success("تم ربط الشريك بنجاح")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('project_home', project_id=project_id))

@app.route('/projects/<project_id>/wallet/<partner_id>/deposit', methods=['POST'])
def deposit_wallet(project_id, partner_id):
    """Deposit to partner wallet"""
    try:
        amount = d(request.form.get('amount'))
        notes = request.form.get('notes')
        
        wallets.deposit_to_wallet(project_id, partner_id, amount, notes)
        
        if request.headers.get('HX-Request'):
            pp = ProjectPartner.query.filter_by(
                project_id=project_id,
                partner_id=partner_id
            ).first()
            return f'<span id="balance-{partner_id}">{format_money(pp.wallet_balance)}</span>'
        
        flash_success(f"تم الإيداع بنجاح: {format_money(amount)}")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('project_home', project_id=project_id))

@app.route('/projects/<project_id>/wallet/<partner_id>/withdraw', methods=['POST'])
def withdraw_wallet(project_id, partner_id):
    """Withdraw from partner wallet"""
    try:
        amount = d(request.form.get('amount'))
        notes = request.form.get('notes')
        
        wallets.withdraw_from_wallet(project_id, partner_id, amount, notes)
        
        if request.headers.get('HX-Request'):
            pp = ProjectPartner.query.filter_by(
                project_id=project_id,
                partner_id=partner_id
            ).first()
            return f'<span id="balance-{partner_id}">{format_money(pp.wallet_balance)}</span>'
        
        flash_success(f"تم السحب بنجاح: {format_money(amount)}")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('project_home', project_id=project_id))

# Stages
@app.route('/projects/<project_id>/stages', methods=['POST'])
def create_stage(project_id):
    """Create new stage"""
    try:
        name = request.form.get('name')
        budget = d(request.form.get('budget', 0))
        
        stage = Stage(
            project_id=project_id,
            name=name,
            budget=budget
        )
        db.session.add(stage)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/stage_row.html', stage=stage)
        
        flash_success("تم إنشاء المرحلة بنجاح")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('project_home', project_id=project_id))

@app.route('/stages/<stage_id>/cost')
def stage_cost_card(stage_id):
    """Get stage cost card"""
    report = reports.generate_stage_cost_report(stage_id)
    if not report:
        return "المرحلة غير موجودة", 404
    
    return render_template('_partials/stage_cost_card.html', report=report)

@app.route('/stages/<stage_id>/allocate/by_share', methods=['POST'])
def allocate_by_share_route(stage_id):
    """Allocate stage costs by partner shares"""
    try:
        allocation = allocations.allocate_by_share(stage_id)
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', 
                                 msg=f"تم توزيع {format_money(allocation.total_amount)} بنجاح",
                                 ok=True)
        
        flash_success(f"تم توزيع التكاليف بنجاح: {format_money(allocation.total_amount)}")
        stage = Stage.query.get(stage_id)
        return redirect(url_for('project_home', project_id=stage.project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        stage = Stage.query.get(stage_id)
        return redirect(url_for('project_home', project_id=stage.project_id))

@app.route('/stages/<stage_id>/allocate/custom', methods=['POST'])
def allocate_custom_route(stage_id):
    """Allocate stage costs with custom amounts"""
    try:
        # Parse custom amounts from form
        custom_amounts = {}
        for key in request.form:
            if key.startswith('amount_'):
                partner_id = key.replace('amount_', '')
                amount = d(request.form[key])
                if amount > 0:
                    custom_amounts[partner_id] = amount
        
        allocation = allocations.allocate_custom(stage_id, custom_amounts)
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg=f"تم توزيع {format_money(allocation.total_amount)} بنجاح",
                                 ok=True)
        
        flash_success(f"تم توزيع التكاليف بنجاح: {format_money(allocation.total_amount)}")
        stage = Stage.query.get(stage_id)
        return redirect(url_for('project_home', project_id=stage.project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        stage = Stage.query.get(stage_id)
        return redirect(url_for('project_home', project_id=stage.project_id))

# Expenses
@app.route('/expenses', methods=['POST'])
def create_expense():
    """Create manual expense"""
    try:
        project_id = request.form.get('project_id')
        stage_id = request.form.get('stage_id') or None
        amount = d(request.form.get('amount'))
        description = request.form.get('description')
        payee_type = request.form.get('payee_type', 'other')
        payee_id = request.form.get('payee_id') or None
        expense_date = parse_date(request.form.get('date')) or date.today()
        
        expense = Expense(
            project_id=project_id,
            stage_id=stage_id,
            date=expense_date,
            amount=amount,
            payee_type=payee_type,
            payee_id=payee_id,
            description=description
        )
        db.session.add(expense)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg=f"تم إضافة المصروف: {format_money(amount)}",
                                 ok=True)
        
        flash_success(f"تم إضافة المصروف: {format_money(amount)}")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(request.referrer or url_for('index'))

# Suppliers
@app.route('/suppliers')
def suppliers_list():
    """List suppliers"""
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('suppliers/list_create.html', suppliers=suppliers)

@app.route('/suppliers', methods=['POST'])
def create_supplier():
    """Create supplier"""
    try:
        name = request.form.get('name')
        
        supplier = Supplier(name=name)
        db.session.add(supplier)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg="تم إضافة المورد بنجاح",
                                 ok=True)
        
        flash_success("تم إضافة المورد بنجاح")
        return redirect(url_for('suppliers_list'))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('suppliers_list'))

# Items
@app.route('/items')
def items_list():
    """List items"""
    items = Item.query.order_by(Item.name).all()
    return render_template('items/list_create.html', items=items)

@app.route('/items', methods=['POST'])
def create_item():
    """Create item"""
    try:
        sku = request.form.get('sku')
        name = request.form.get('name')
        uom = request.form.get('uom', 'unit')
        std_cost = d(request.form.get('std_cost', 0))
        
        # Check if SKU exists
        if Item.query.filter_by(sku=sku).first():
            raise ValidationError("كود الصنف موجود بالفعل")
        
        item = Item(
            sku=sku,
            name=name,
            uom=uom,
            std_cost=std_cost
        )
        db.session.add(item)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg="تم إضافة الصنف بنجاح",
                                 ok=True)
        
        flash_success("تم إضافة الصنف بنجاح")
        return redirect(url_for('items_list'))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('items_list'))

# Warehouses
@app.route('/projects/<project_id>/warehouses', methods=['POST'])
def create_warehouse(project_id):
    """Create warehouse"""
    try:
        name = request.form.get('name')
        
        warehouse = Warehouse(
            project_id=project_id,
            name=name
        )
        db.session.add(warehouse)
        db.session.commit()
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg="تم إنشاء المخزن بنجاح",
                                 ok=True)
        
        flash_success("تم إنشاء المخزن بنجاح")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('project_home', project_id=project_id))

# Purchases
@app.route('/purchases/invoices/new')
def new_purchase_invoice():
    """New purchase invoice form"""
    projects = Project.query.all()
    suppliers = Supplier.query.all()
    items = Item.query.all()
    return render_template('purchases/create_invoice.html',
                         projects=projects,
                         suppliers=suppliers,
                         items=items)

@app.route('/purchases/invoices', methods=['POST'])
def create_purchase_invoice():
    """Create purchase invoice"""
    try:
        project_id = request.form.get('project_id')
        supplier_id = request.form.get('supplier_id')
        invoice_date = parse_date(request.form.get('date')) or date.today()
        
        # Parse items
        items_data = []
        item_count = int(request.form.get('item_count', 0))
        for i in range(item_count):
            item_id = request.form.get(f'item_id_{i}')
            if item_id:
                items_data.append({
                    'item_id': item_id,
                    'qty': request.form.get(f'qty_{i}'),
                    'unit_cost': request.form.get(f'unit_cost_{i}'),
                    'tax': request.form.get(f'tax_{i}', 0)
                })
        
        if not items_data:
            raise ValidationError("يجب إضافة صنف واحد على الأقل")
        
        # Get warehouse
        warehouse = Warehouse.query.filter_by(project_id=project_id).first()
        if not warehouse:
            # Create default warehouse
            warehouse = Warehouse(project_id=project_id, name="المخزن الرئيسي")
            db.session.add(warehouse)
            db.session.flush()
        
        invoice = purchases.create_purchase_invoice(
            project_id, supplier_id, invoice_date, items_data, warehouse.id
        )
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg=f"تم إنشاء الفاتورة بنجاح. الإجمالي: {format_money(invoice.total)}",
                                 ok=True)
        
        flash_success(f"تم إنشاء الفاتورة بنجاح. الإجمالي: {format_money(invoice.total)}")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('new_purchase_invoice'))

# Stock
@app.route('/stock/issue', methods=['GET', 'POST'])
def stock_issue():
    """Stock issue form and processing"""
    if request.method == 'GET':
        projects = Project.query.all()
        return render_template('stock/issue.html', projects=projects)
    
    try:
        project_id = request.form.get('project_id')
        warehouse_id = request.form.get('warehouse_id')
        stage_id = request.form.get('stage_id')
        item_id = request.form.get('item_id')
        qty = d(request.form.get('qty'))
        issue_date = parse_date(request.form.get('date')) or date.today()
        
        move, expense = stock.issue_stock_to_stage(
            project_id, warehouse_id, stage_id, item_id, qty, issue_date
        )
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg=f"تم صرف المواد بنجاح. القيمة: {format_money(expense.amount)}",
                                 ok=True)
        
        flash_success(f"تم صرف المواد بنجاح. القيمة: {format_money(expense.amount)}")
        return redirect(url_for('project_home', project_id=project_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('stock_issue'))

# Settlements
@app.route('/settlements')
def settlements_list():
    """List settlement batches"""
    project_id = request.args.get('project_id')
    
    query = PartnerSettleBatch.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    batches = query.order_by(PartnerSettleBatch.created_at.desc()).all()
    projects = Project.query.all()
    
    return render_template('settlements/list.html',
                         batches=batches,
                         projects=projects,
                         selected_project_id=project_id)

@app.route('/settlements', methods=['POST'])
def create_settlement():
    """Create settlement preview"""
    try:
        project_id = request.form.get('project_id')
        cutoff_date = parse_date(request.form.get('cutoff_date'))
        
        if not cutoff_date:
            raise ValidationError("يجب تحديد تاريخ القطع")
        
        batch = settlements.create_settlement_preview(project_id, cutoff_date)
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/settlement_preview.html', batch=batch)
        
        return redirect(url_for('settlement_details', batch_id=batch.id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('settlements_list'))

@app.route('/settlements/<batch_id>')
def settlement_details(batch_id):
    """Settlement batch details"""
    batch = PartnerSettleBatch.query.get_or_404(batch_id)
    return render_template('settlements/details.html', batch=batch)

@app.route('/settlements/<batch_id>/post', methods=['POST'])
def post_settlement(batch_id):
    """Post settlement batch"""
    try:
        batch = settlements.post_settlement(batch_id)
        
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html',
                                 msg="تم ترحيل التسوية بنجاح",
                                 ok=True)
        
        flash_success("تم ترحيل التسوية بنجاح")
        return redirect(url_for('settlement_details', batch_id=batch_id))
    
    except Exception as e:
        if request.headers.get('HX-Request'):
            return render_template('_partials/toast.html', msg=str(e), ok=False)
        flash_error(str(e))
        return redirect(url_for('settlement_details', batch_id=batch_id))

# Reports
@app.route('/reports/partner-statement')
def partner_statement():
    """Partner statement report"""
    project_id = request.args.get('project_id')
    partner_id = request.args.get('partner_id')
    from_date = parse_date(request.args.get('from'))
    to_date = parse_date(request.args.get('to'))
    
    if not project_id or not partner_id:
        projects = Project.query.all()
        partners = Partner.query.all()
        return render_template('reports/partner_statement.html',
                             projects=projects,
                             partners=partners)
    
    statement = reports.generate_partner_statement(
        project_id, partner_id, from_date, to_date
    )
    
    if not statement:
        flash_error("الشريك غير مرتبط بالمشروع")
        return redirect(url_for('partner_statement'))
    
    # Check if CSV export requested
    if request.headers.get('Accept') == 'text/csv':
        csv_data = reports.export_partner_statement_csv(statement)
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=statement_{partner_id}.csv'
        return response
    
    return render_template('reports/partner_statement.html',
                         statement=statement,
                         from_date=from_date,
                         to_date=to_date)

# API endpoints for HTMX
@app.route('/api/projects/<project_id>/stages')
def api_project_stages(project_id):
    """Get project stages as JSON"""
    stages = Stage.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name
    } for s in stages])

@app.route('/api/projects/<project_id>/warehouses')
def api_project_warehouses(project_id):
    """Get project warehouses as JSON"""
    warehouses = Warehouse.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'id': w.id,
        'name': w.name
    } for w in warehouses])

@app.route('/api/warehouses/<warehouse_id>/items')
def api_warehouse_items(warehouse_id):
    """Get items with stock in warehouse"""
    summary = stock.get_warehouse_stock_summary(warehouse_id)
    return jsonify([{
        'id': s['item'].id,
        'name': f"{s['item'].name} ({s['balance']} {s['item'].uom})"
    } for s in summary])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)