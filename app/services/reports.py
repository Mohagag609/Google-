"""Reporting service"""
from ..db import db
from ..models import (
    ProjectPartner, Voucher, Allocation, Expense,
    Stage, StockMove, PartnerSettleLine
)
from ..utils import d
from decimal import Decimal
import csv
from io import StringIO

def generate_partner_statement(project_id, partner_id, from_date=None, to_date=None):
    """Generate partner statement with movements and balance"""
    pp = ProjectPartner.query.filter_by(
        project_id=project_id,
        partner_id=partner_id
    ).first()
    
    if not pp:
        return None
    
    movements = []
    running_balance = Decimal("0")
    
    # Add carry forward if exists
    if pp.carry_forward_balance != 0:
        movements.append({
            'date': None,
            'type': 'رصيد مرحل',
            'description': 'رصيد مرحل من تسويات سابقة',
            'debit': d(pp.carry_forward_balance) if pp.carry_forward_balance > 0 else Decimal("0"),
            'credit': abs(d(pp.carry_forward_balance)) if pp.carry_forward_balance < 0 else Decimal("0"),
            'balance': d(pp.carry_forward_balance)
        })
        running_balance = d(pp.carry_forward_balance)
    
    # Get vouchers (deposits and withdrawals)
    vouchers_query = Voucher.query.filter_by(
        project_id=project_id,
        party_type='partner',
        party_id=partner_id
    )
    
    if from_date:
        vouchers_query = vouchers_query.filter(Voucher.v_date >= from_date)
    if to_date:
        vouchers_query = vouchers_query.filter(Voucher.v_date <= to_date)
    
    vouchers = vouchers_query.order_by(Voucher.v_date).all()
    
    for voucher in vouchers:
        if voucher.v_type == 'receipt':
            running_balance += d(voucher.amount)
            movements.append({
                'date': voucher.v_date,
                'type': 'إيداع',
                'description': voucher.notes or f'إيداع - {voucher.ref_code}',
                'debit': d(voucher.amount),
                'credit': Decimal("0"),
                'balance': running_balance
            })
        else:  # payment
            running_balance -= d(voucher.amount)
            movements.append({
                'date': voucher.v_date,
                'type': 'سحب',
                'description': voucher.notes or f'سحب - {voucher.ref_code}',
                'debit': Decimal("0"),
                'credit': d(voucher.amount),
                'balance': running_balance
            })
    
    # Get allocations
    allocations_query = Allocation.query.filter_by(
        project_id=project_id,
        posted=True
    )
    
    if from_date:
        allocations_query = allocations_query.filter(Allocation.alloc_date >= from_date)
    if to_date:
        allocations_query = allocations_query.filter(Allocation.alloc_date <= to_date)
    
    allocations = allocations_query.order_by(Allocation.alloc_date).all()
    
    for allocation in allocations:
        details = allocation.details
        if partner_id in details:
            amount = d(details[partner_id])
            running_balance -= amount
            movements.append({
                'date': allocation.alloc_date,
                'type': 'توزيع تكاليف',
                'description': f'توزيع تكاليف - {allocation.stage.name}',
                'debit': Decimal("0"),
                'credit': amount,
                'balance': running_balance
            })
    
    # Get direct expenses
    expenses_query = Expense.query.filter_by(
        project_id=project_id,
        payee_type='partner',
        payee_id=partner_id
    )
    
    if from_date:
        expenses_query = expenses_query.filter(Expense.date >= from_date)
    if to_date:
        expenses_query = expenses_query.filter(Expense.date <= to_date)
    
    expenses = expenses_query.order_by(Expense.date).all()
    
    for expense in expenses:
        running_balance += d(expense.amount)
        movements.append({
            'date': expense.date,
            'type': 'مصروف مباشر',
            'description': expense.description or 'مصروف مباشر',
            'debit': d(expense.amount),
            'credit': Decimal("0"),
            'balance': running_balance
        })
    
    # Sort movements by date
    movements.sort(key=lambda x: x['date'] if x['date'] else '')
    
    return {
        'partner': pp.partner,
        'project': pp.project,
        'movements': movements,
        'final_balance': running_balance,
        'wallet_balance': d(pp.wallet_balance),
        'carry_forward': d(pp.carry_forward_balance)
    }

def generate_stage_cost_report(stage_id):
    """Generate detailed cost report for a stage"""
    stage = Stage.query.get(stage_id)
    if not stage:
        return None
    
    # Get expenses
    expenses = Expense.query.filter_by(stage_id=stage_id).order_by(Expense.date).all()
    
    # Get stock issues
    stock_moves = StockMove.query.filter(
        StockMove.stage_id == stage_id,
        StockMove.qty_out > 0
    ).order_by(StockMove.move_date).all()
    
    # Get allocations
    allocations = Allocation.query.filter_by(
        stage_id=stage_id,
        posted=True
    ).order_by(Allocation.alloc_date).all()
    
    # Calculate totals
    total_expenses = sum(d(e.amount) for e in expenses)
    total_stock = sum(d(s.amount) for s in stock_moves)
    total_allocated = sum(d(a.total_amount) for a in allocations)
    total_cost = total_expenses + total_stock
    unallocated = total_cost - total_allocated
    
    return {
        'stage': stage,
        'expenses': expenses,
        'stock_moves': stock_moves,
        'allocations': allocations,
        'total_expenses': total_expenses,
        'total_stock': total_stock,
        'total_cost': total_cost,
        'total_allocated': total_allocated,
        'unallocated': unallocated,
        'budget': d(stage.budget),
        'variance': d(stage.budget) - total_cost if stage.budget else None
    }

def export_partner_statement_csv(statement_data):
    """Export partner statement to CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['التاريخ', 'النوع', 'الوصف', 'مدين', 'دائن', 'الرصيد'])
    
    # Write movements
    for movement in statement_data['movements']:
        writer.writerow([
            movement['date'].strftime('%Y-%m-%d') if movement['date'] else '',
            movement['type'],
            movement['description'],
            movement['debit'],
            movement['credit'],
            movement['balance']
        ])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['الملخص', '', '', '', '', ''])
    writer.writerow(['الرصيد النهائي', '', '', '', '', statement_data['final_balance']])
    writer.writerow(['رصيد المحفظة', '', '', '', '', statement_data['wallet_balance']])
    writer.writerow(['الرصيد المرحل', '', '', '', '', statement_data['carry_forward']])
    
    output.seek(0)
    return output.getvalue()

def get_project_summary(project_id):
    """Get project financial summary"""
    # Total costs
    total_expenses = db.session.query(
        db.func.sum(Expense.amount)
    ).filter_by(project_id=project_id).scalar() or Decimal("0")
    
    total_stock_issued = db.session.query(
        db.func.sum(StockMove.amount)
    ).filter(
        StockMove.project_id == project_id,
        StockMove.qty_out > 0
    ).scalar() or Decimal("0")
    
    # Total allocations
    total_allocated = db.session.query(
        db.func.sum(Allocation.total_amount)
    ).filter(
        Allocation.project_id == project_id,
        Allocation.posted == True
    ).scalar() or Decimal("0")
    
    # Partner wallets
    total_wallets = db.session.query(
        db.func.sum(ProjectPartner.wallet_balance)
    ).filter_by(project_id=project_id).scalar() or Decimal("0")
    
    # Stages summary
    stages = Stage.query.filter_by(project_id=project_id).all()
    stages_summary = []
    for stage in stages:
        report = generate_stage_cost_report(stage.id)
        stages_summary.append({
            'stage': stage,
            'total_cost': report['total_cost'],
            'allocated': report['total_allocated'],
            'unallocated': report['unallocated']
        })
    
    return {
        'total_expenses': d(total_expenses),
        'total_stock_issued': d(total_stock_issued),
        'total_cost': d(total_expenses) + d(total_stock_issued),
        'total_allocated': d(total_allocated),
        'total_wallets': d(total_wallets),
        'stages': stages_summary
    }