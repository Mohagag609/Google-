"""Purchase invoice and stock-in service"""
from db import db
from models import PurchaseInvoice, PurchaseInvoiceItem, StockMove, Warehouse
from utils import d, ValidationError
from datetime import date
from decimal import Decimal

def create_purchase_invoice(project_id, supplier_id, invoice_date, items_data, warehouse_id=None):
    """Create purchase invoice and stock moves"""
    # Get default warehouse if not specified
    if not warehouse_id:
        warehouse = Warehouse.query.filter_by(project_id=project_id).first()
        if not warehouse:
            raise ValidationError("لا يوجد مخزن في المشروع")
        warehouse_id = warehouse.id
    
    # Create invoice header
    invoice = PurchaseInvoice(
        project_id=project_id,
        supplier_id=supplier_id,
        date=invoice_date,
        total=Decimal("0"),
        status='posted'
    )
    db.session.add(invoice)
    db.session.flush()
    
    total = Decimal("0")
    
    # Create invoice items and stock moves
    for item_data in items_data:
        item_id = item_data['item_id']
        qty = d(item_data['qty'])
        unit_cost = d(item_data['unit_cost'])
        tax = d(item_data.get('tax', 0))
        
        # Create invoice item
        invoice_item = PurchaseInvoiceItem(
            invoice_id=invoice.id,
            item_id=item_id,
            qty=qty,
            unit_cost=unit_cost,
            tax=tax
        )
        db.session.add(invoice_item)
        
        # Calculate line total
        line_total = (qty * unit_cost) + tax
        total += line_total
        
        # Create stock move (stock-in)
        stock_move = StockMove(
            project_id=project_id,
            warehouse_id=warehouse_id,
            item_id=item_id,
            qty_in=qty,
            qty_out=Decimal("0"),
            unit_cost=unit_cost,
            amount=qty * unit_cost,
            ref_type='PI',
            ref_id=invoice.id,
            move_date=invoice_date
        )
        db.session.add(stock_move)
    
    # Update invoice total
    invoice.total = d(total)
    
    db.session.commit()
    return invoice

def get_invoice_details(invoice_id):
    """Get purchase invoice with items"""
    invoice = PurchaseInvoice.query.get(invoice_id)
    if not invoice:
        return None
    
    return {
        'invoice': invoice,
        'items': invoice.items,
        'supplier': invoice.supplier,
        'project': invoice.project
    }

def cancel_purchase_invoice(invoice_id):
    """Cancel purchase invoice and reverse stock moves"""
    invoice = PurchaseInvoice.query.get(invoice_id)
    if not invoice:
        raise ValidationError("الفاتورة غير موجودة")
    
    if invoice.status == 'cancelled':
        raise ValidationError("الفاتورة ملغاة بالفعل")
    
    # Delete related stock moves
    StockMove.query.filter_by(ref_type='PI', ref_id=invoice_id).delete()
    
    # Update invoice status
    invoice.status = 'cancelled'
    
    db.session.commit()
    return invoice