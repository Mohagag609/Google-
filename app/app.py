#!/usr/bin/env python3
"""
Musharaka Pro - Flask Application
"""

import os
from datetime import datetime, date
from decimal import Decimal
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.exceptions import BadRequest

from db import init_db
from models import *
from services import *
from forms import *
from utils import d, ValidationError, BusinessRuleError

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize database
    init_db(app)
    
    # Error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return render_template('_partials/toast.html', 
                             message=str(e), success=False), 400
    
    @app.errorhandler(BusinessRuleError)
    def handle_business_rule_error(e):
        return render_template('_partials/toast.html', 
                             message=str(e), success=False), 400
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template('_partials/toast.html', 
                             message="الصفحة غير موجودة", success=False), 404
    
    # Routes
    @app.route('/')
    def index():
        """Home page with projects list."""
        projects = ProjectService.get_all_projects()
        partners = PartnerService.get_all_partners()
        return render_template('projects/index.html', 
                             projects=projects, partners=partners)
    
    @app.route('/projects', methods=['POST'])
    def create_project():
        """Create a new project."""
        try:
            data = ProjectForm.validate_create(request.form.to_dict())
            project = ProjectService.create_project(
                code=data['code'],
                name=data['name'],
                base_currency=data['base_currency']
            )
            return render_template('_partials/project_row.html', project=project)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/projects/<project_id>')
    def project_home(project_id):
        """Project home page."""
        project = ProjectService.get_project(project_id)
        if not project:
            return render_template('_partials/toast.html', 
                                 message="المشروع غير موجود", success=False), 404
        
        project_partners = PartnerService.get_project_partners(project_id)
        stages = Stage.query.filter_by(project_id=project_id).all()
        available_partners = Partner.query.filter(
            ~Partner.id.in_([pp.partner_id for pp in project_partners])
        ).all()
        
        return render_template('projects/project_home.html',
                             project=project,
                             project_partners=project_partners,
                             stages=stages,
                             available_partners=available_partners)
    
    @app.route('/partners', methods=['POST'])
    def create_partner():
        """Create a new partner."""
        try:
            data = PartnerForm.validate_create(request.form.to_dict())
            partner = PartnerService.create_partner(name=data['name'])
            return render_template('_partials/partner_option.html', partner=partner)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/projects/<project_id>/partners/link', methods=['POST'])
    def link_partner_to_project(project_id):
        """Link partner to project."""
        try:
            data = PartnerForm.validate_link(request.form.to_dict())
            project_partner = PartnerService.link_partner_to_project(
                project_id=project_id,
                partner_id=data['partner_id'],
                share_pct=data['share_pct']
            )
            project = ProjectService.get_project(project_id)
            return render_template('_partials/partner_link_row.html', 
                                 project_partner=project_partner, project=project)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/projects/<project_id>/wallet/<partner_id>/deposit', methods=['POST'])
    def deposit_to_wallet(project_id, partner_id):
        """Deposit money to partner wallet."""
        try:
            data = WalletForm.validate_transaction(request.form.to_dict())
            voucher = WalletService.deposit(
                project_id=project_id,
                partner_id=partner_id,
                amount=data['amount'],
                notes=data['notes']
            )
            return render_template('_partials/toast.html', 
                                 message=f"تم إيداع {d(data['amount'])} بنجاح", success=True)
        except (ValidationError, BusinessRuleError) as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/projects/<project_id>/wallet/<partner_id>/withdraw', methods=['POST'])
    def withdraw_from_wallet(project_id, partner_id):
        """Withdraw money from partner wallet."""
        try:
            data = WalletForm.validate_transaction(request.form.to_dict())
            voucher = WalletService.withdraw(
                project_id=project_id,
                partner_id=partner_id,
                amount=data['amount'],
                notes=data['notes']
            )
            return render_template('_partials/toast.html', 
                                 message=f"تم سحب {d(data['amount'])} بنجاح", success=True)
        except (ValidationError, BusinessRuleError) as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/projects/<project_id>/stages', methods=['POST'])
    def create_stage(project_id):
        """Create a new stage."""
        try:
            data = StageForm.validate_create(request.form.to_dict())
            stage = StageService.create_stage(
                project_id=project_id,
                name=data['name'],
                budget=data['budget']
            )
            return render_template('_partials/stage_row.html', stage=stage)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/stages/<stage_id>/cost')
    def get_stage_cost(stage_id):
        """Get stage cost information."""
        try:
            cost_info = StageService.get_stage_cost(stage_id)
            return render_template('_partials/stage_cost_card.html', cost_info=cost_info)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/stages/<stage_id>/allocate/by_share', methods=['POST'])
    def allocate_by_share(stage_id):
        """Allocate stage cost by partner shares."""
        try:
            allocation = AllocationService.allocate_by_share(stage_id)
            return render_template('_partials/toast.html', 
                                 message="تم توزيع التكلفة بالنسب بنجاح", success=True)
        except (ValidationError, BusinessRuleError) as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/stages/<stage_id>/allocate/custom', methods=['POST'])
    def allocate_custom(stage_id):
        """Allocate stage cost with custom amounts."""
        try:
            data = AllocationForm.validate_custom(request.form.to_dict())
            allocation = AllocationService.allocate_custom(
                stage_id=stage_id,
                partner_amounts=data['partner_amounts']
            )
            return render_template('_partials/toast.html', 
                                 message="تم توزيع التكلفة بنجاح", success=True)
        except (ValidationError, BusinessRuleError) as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    # Additional routes for suppliers, items, warehouses
    @app.route('/suppliers', methods=['POST'])
    def create_supplier():
        """Create a new supplier."""
        try:
            data = request.form.to_dict()
            FormValidator.validate_required(data, ['name'])
            
            supplier = Supplier(name=data['name'].strip())
            db.session.add(supplier)
            db.session.commit()
            
            return render_template('_partials/toast.html', 
                                 message="تم إنشاء المورد بنجاح", success=True)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/items', methods=['POST'])
    def create_item():
        """Create a new item."""
        try:
            data = request.form.to_dict()
            FormValidator.validate_required(data, ['sku', 'name'])
            
            # Check if SKU already exists
            existing = Item.query.filter_by(sku=data['sku']).first()
            if existing:
                raise ValidationError("كود الصنف موجود بالفعل")
            
            item = Item(
                sku=data['sku'].strip(),
                name=data['name'].strip(),
                uom=data.get('uom', 'unit'),
                std_cost=FormValidator.validate_positive_decimal(data.get('std_cost', 0))
            )
            
            db.session.add(item)
            db.session.commit()
            
            return render_template('_partials/toast.html', 
                                 message="تم إنشاء الصنف بنجاح", success=True)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    @app.route('/projects/<project_id>/warehouses', methods=['POST'])
    def create_warehouse(project_id):
        """Create a new warehouse."""
        try:
            data = request.form.to_dict()
            FormValidator.validate_required(data, ['name'])
            
            warehouse = Warehouse(
                project_id=project_id,
                name=data['name'].strip()
            )
            
            db.session.add(warehouse)
            db.session.commit()
            
            return render_template('_partials/toast.html', 
                                 message="تم إنشاء المستودع بنجاح", success=True)
        except ValidationError as e:
            return render_template('_partials/toast.html', 
                                 message=str(e), success=False), 400
    
    # API endpoints for JSON responses
    @app.route('/api/projects')
    def api_projects():
        """API endpoint to get all projects."""
        projects = ProjectService.get_all_projects()
        return jsonify({
            'ok': True,
            'data': [{
                'id': p.id,
                'code': p.code,
                'name': p.name,
                'base_currency': p.base_currency,
                'status': p.status,
                'created_at': p.created_at.isoformat()
            } for p in projects]
        })
    
    @app.route('/api/partners')
    def api_partners():
        """API endpoint to get all partners."""
        partners = PartnerService.get_all_partners()
        return jsonify({
            'ok': True,
            'data': [{
                'id': p.id,
                'name': p.name,
                'created_at': p.created_at.isoformat()
            } for p in partners]
        })
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)