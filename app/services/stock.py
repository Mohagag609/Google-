"""Stock management service"""
from ..db import db
from ..models import StockMove, Item, Expense, Warehouse
from ..utils import d, ValidationError
from datetime import date
from decimal import Decimal

def get_item_stock_balance(project_id, item_id, warehouse_id=None):
    """Get current stock balance for an item"""
    query = StockMove.query.filter_by(
        project_id=project_id,
        item_id=item_id
    )
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    
    # Sum qty_in
    total_in = db.session.query(
        db.func.sum(StockMove.qty_in)
    ).filter_by(
        project_id=project_id,
        item_id=item_id
    ).scalar() or Decimal("0")
    
    # Sum qty_out
    total_out = db.session.query(
        db.func.sum(StockMove.qty_out)
    ).filter_by(
        project_id=project_id,
        item_id=item_id
    ).scalar() or Decimal("0")
    
    if warehouse_id:
        total_in = db.session.query(
            db.func.sum(StockMove.qty_in)
        ).filter_by(
            project_id=project_id,
            item_id=item_id,
            warehouse_id=warehouse_id
        ).scalar() or Decimal("0")
        
        total_out = db.session.query(
            db.func.sum(StockMove.qty_out)
        ).filter_by(
            project_id=project_id,
            item_id=item_id,
            warehouse_id=warehouse_id
        ).scalar() or Decimal("0")
    
    return d(total_in) - d(total_out)

def issue_stock_to_stage(project_id, warehouse_id, stage_id, item_id, qty, issue_date=None):
    """Issue stock to a stage and create expense"""
    qty = d(qty)
    if qty <= 0:
        raise ValidationError("الكمية يجب أن تكون أكبر من صفر")
    
    # Check available stock
    available = get_item_stock_balance(project_id, item_id, warehouse_id)
    if available < qty:
        raise ValidationError(f"الكمية المتاحة غير كافية. المتاح: {available}")
    
    # Get item for standard cost
    item = Item.query.get(item_id)
    if not item:
        raise ValidationError("الصنف غير موجود")
    
    # Calculate amount
    amount = d(qty * item.std_cost)
    
    # Create stock move (issue)
    stock_move = StockMove(
        project_id=project_id,
        warehouse_id=warehouse_id,
        item_id=item_id,
        qty_in=Decimal("0"),
        qty_out=qty,
        unit_cost=item.std_cost,
        amount=amount,
        ref_type='ISSUE',
        stage_id=stage_id,
        move_date=issue_date or date.today()
    )
    db.session.add(stock_move)
    
    # Create expense for the stage
    expense = Expense(
        project_id=project_id,
        stage_id=stage_id,
        date=issue_date or date.today(),
        amount=amount,
        payee_type='other',
        description=f"صرف مواد: {item.name} ({qty} {item.uom})"
    )
    db.session.add(expense)
    
    db.session.commit()
    return stock_move, expense

def get_stock_movements(project_id, item_id=None, warehouse_id=None, from_date=None, to_date=None):
    """Get stock movements with filters"""
    query = StockMove.query.filter_by(project_id=project_id)
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if from_date:
        query = query.filter(StockMove.move_date >= from_date)
    if to_date:
        query = query.filter(StockMove.move_date <= to_date)
    
    return query.order_by(StockMove.move_date.desc()).all()

def get_warehouse_stock_summary(warehouse_id):
    """Get stock summary for a warehouse"""
    # Get all items with movements in this warehouse
    items_query = db.session.query(
        StockMove.item_id,
        db.func.sum(StockMove.qty_in).label('total_in'),
        db.func.sum(StockMove.qty_out).label('total_out')
    ).filter_by(
        warehouse_id=warehouse_id
    ).group_by(StockMove.item_id)
    
    summary = []
    for row in items_query:
        item = Item.query.get(row.item_id)
        balance = d(row.total_in or 0) - d(row.total_out or 0)
        if balance != 0:  # Only show items with balance
            summary.append({
                'item': item,
                'balance': balance,
                'value': d(balance * item.std_cost)
            })
    
    return summary