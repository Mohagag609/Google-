"""Backup and restore service"""
import os
import json
import zipfile
from datetime import datetime
from io import BytesIO
from db import db
from models import *
from decimal import Decimal
from datetime import date
import csv

def create_backup():
    """Create a complete backup of the database"""
    backup_data = {
        'version': '1.0',
        'created_at': datetime.utcnow().isoformat(),
        'tables': {}
    }
    
    # List of models to backup
    models_to_backup = [
        Project, Partner, ProjectPartner, Supplier, Item, Warehouse,
        Stage, PurchaseInvoice, PurchaseInvoiceItem, StockMove,
        Expense, Voucher, Allocation, PartnerSettleBatch,
        PartnerSettleLine, PartnerClaim
    ]
    
    for model in models_to_backup:
        table_name = model.__tablename__
        records = []
        
        for record in model.query.all():
            record_dict = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                # Convert special types to string
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, date):
                    value = value.isoformat()
                elif isinstance(value, Decimal):
                    value = str(value)
                record_dict[column.name] = value
            records.append(record_dict)
        
        backup_data['tables'][table_name] = records
    
    # Create ZIP file with JSON data
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add main backup JSON
        zip_file.writestr('backup.json', json.dumps(backup_data, ensure_ascii=False, indent=2))
        
        # Add metadata
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'total_projects': Project.query.count(),
            'total_partners': Partner.query.count(),
            'total_expenses': db.session.query(db.func.sum(Expense.amount)).scalar() or 0
        }
        zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
    
    zip_buffer.seek(0)
    return zip_buffer

def restore_backup(backup_file):
    """Restore database from backup file"""
    try:
        # Read ZIP file
        with zipfile.ZipFile(backup_file, 'r') as zip_file:
            # Read backup data
            backup_json = zip_file.read('backup.json')
            backup_data = json.loads(backup_json)
        
        # Verify version
        if backup_data.get('version') != '1.0':
            raise ValueError("إصدار النسخة الاحتياطية غير متوافق")
        
        # Clear existing data (be careful!)
        # This should be done in a transaction
        db.session.rollback()
        
        # Disable foreign key constraints temporarily
        db.session.execute('PRAGMA foreign_keys=OFF')
        
        # Delete in reverse order to avoid foreign key issues
        models_to_clear = [
            PartnerClaim, PartnerSettleLine, PartnerSettleBatch,
            Allocation, Voucher, Expense, StockMove,
            PurchaseInvoiceItem, PurchaseInvoice, Stage,
            Warehouse, Item, Supplier, ProjectPartner,
            Partner, Project
        ]
        
        for model in models_to_clear:
            model.query.delete()
        
        db.session.commit()
        
        # Restore data in correct order
        models_order = [
            (Project, 'projects'),
            (Partner, 'partners'),
            (ProjectPartner, 'project_partners'),
            (Supplier, 'suppliers'),
            (Item, 'items'),
            (Warehouse, 'warehouses'),
            (Stage, 'stages'),
            (PurchaseInvoice, 'purchase_invoices'),
            (PurchaseInvoiceItem, 'purchase_invoice_items'),
            (StockMove, 'stock_moves'),
            (Expense, 'expenses'),
            (Voucher, 'vouchers'),
            (Allocation, 'allocations'),
            (PartnerSettleBatch, 'partner_settle_batches'),
            (PartnerSettleLine, 'partner_settle_lines'),
            (PartnerClaim, 'partner_claims')
        ]
        
        for model, table_name in models_order:
            if table_name in backup_data['tables']:
                for record_data in backup_data['tables'][table_name]:
                    # Convert string dates back to datetime/date objects
                    for column in model.__table__.columns:
                        if column.name in record_data:
                            value = record_data[column.name]
                            if value is not None:
                                if column.type.__class__.__name__ == 'DateTime':
                                    record_data[column.name] = datetime.fromisoformat(value)
                                elif column.type.__class__.__name__ == 'Date':
                                    record_data[column.name] = datetime.fromisoformat(value).date()
                                elif column.type.__class__.__name__ == 'Numeric':
                                    record_data[column.name] = Decimal(value)
                    
                    # Create new record
                    record = model(**record_data)
                    db.session.add(record)
        
        # Re-enable foreign key constraints
        db.session.execute('PRAGMA foreign_keys=ON')
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"فشل استعادة النسخة الاحتياطية: {str(e)}")

def export_to_csv(model, query=None):
    """Export model data to CSV"""
    if query is None:
        query = model.query
    
    output = BytesIO()
    writer = csv.writer(output)
    
    # Write headers
    columns = [column.name for column in model.__table__.columns]
    writer.writerow(columns)
    
    # Write data
    for record in query.all():
        row = []
        for column in columns:
            value = getattr(record, column)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = str(value)
            row.append(value)
        writer.writerow(row)
    
    output.seek(0)
    return output

def get_database_stats():
    """Get database statistics"""
    stats = {
        'projects': {
            'total': Project.query.count(),
            'active': Project.query.filter_by(status='open').count()
        },
        'partners': {
            'total': Partner.query.count(),
            'with_projects': db.session.query(db.func.count(db.func.distinct(ProjectPartner.partner_id))).scalar()
        },
        'financial': {
            'total_expenses': db.session.query(db.func.sum(Expense.amount)).scalar() or 0,
            'total_purchases': db.session.query(db.func.sum(PurchaseInvoice.total)).scalar() or 0,
            'total_wallets': db.session.query(db.func.sum(ProjectPartner.wallet_balance)).scalar() or 0
        },
        'inventory': {
            'total_items': Item.query.count(),
            'total_warehouses': Warehouse.query.count(),
            'total_movements': StockMove.query.count()
        },
        'database': {
            'size_mb': get_database_size(),
            'last_backup': get_last_backup_date()
        }
    }
    return stats

def get_database_size():
    """Get database file size in MB"""
    try:
        db_path = db.engine.url.database
        if db_path and os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            return round(size_bytes / (1024 * 1024), 2)
    except:
        pass
    return 0

def get_last_backup_date():
    """Get last backup date from backup directory"""
    # This would check a backup directory for the most recent backup
    # For now, return None
    return None