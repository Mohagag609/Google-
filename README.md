# Musharaka Pro - Project Finance Management System

A Flask-based backend system for managing project finance with partner shares, wallet management, stock tracking, and inter-partner settlements.

## Features

- **Project Management**: Create and manage projects with partner allocations
- **Partner Wallets**: Deposit/withdraw funds with automatic balance tracking
- **Stock Management**: Purchase invoices, stock movements, and material cost tracking
- **Stage Management**: Track project stages with budget and cost allocation
- **Expense Tracking**: Record various types of expenses
- **Cost Allocation**: Allocate stage costs to partners by share or custom amounts
- **Settlement System**: Generate inter-partner settlements with claims and carry-forward balances
- **Reporting**: Partner statements and cost breakdowns

## Installation

1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python app.py
```

The application will start on `http://localhost:5000` with debug mode enabled.

## Database

- Default: SQLite (`musharaka.db`)
- To use PostgreSQL, set the `DATABASE_URL` environment variable:
  ```bash
  export DATABASE_URL="postgresql://user:password@localhost/musharaka"
  ```

## API Endpoints

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects

### Partners
- `POST /api/partners` - Create partner
- `POST /api/projects/{project_id}/partners` - Add partner to project

### Wallet Management
- `POST /api/projects/{project_id}/partners/{partner_id}/wallet/deposit` - Deposit funds
- `POST /api/projects/{project_id}/partners/{partner_id}/wallet/withdraw` - Withdraw funds

### Inventory & Purchases
- `POST /api/suppliers` - Create supplier
- `POST /api/items` - Create item
- `POST /api/projects/{project_id}/warehouses` - Create warehouse
- `POST /api/purchases/invoices` - Create purchase invoice
- `POST /api/stock/issue` - Issue stock to stage

### Stages & Expenses
- `POST /api/projects/{project_id}/stages` - Create stage
- `POST /api/expenses` - Create expense
- `GET /api/stages/{stage_id}/cost` - Get stage cost breakdown
- `POST /api/stages/{stage_id}/allocate` - Allocate stage costs

### Settlements
- `POST /api/settlements` - Create settlement batch
- `POST /api/settlements/{batch_id}/post` - Post settlement
- `GET /api/settlements/{batch_id}` - Get settlement details

### Reports
- `GET /api/reports/partner-statement` - Get partner statement

## Business Rules

1. **Partner Shares**: Must total exactly 100% per project
2. **Wallet Operations**: Withdrawals require sufficient balance
3. **Cost Allocation**: Delta-based allocation (total cost - already allocated)
4. **Settlements**: Greedy matching of debtors to creditors
5. **Monetary Values**: All amounts stored as Decimal with 2 decimal places

## Example Flow

1. Create project and add partners with shares
2. Deposit funds to partner wallets
3. Create suppliers, items, and warehouses
4. Record purchase invoices (stock-in)
5. Issue materials to stages (creates expenses)
6. Record additional stage expenses
7. Allocate stage costs to partners
8. Generate settlement batch and post

## Response Format

All API responses follow this format:

**Success:**
```json
{
  "ok": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "ok": false,
  "error_code": "ERROR_CODE",
  "message": "Error description",
  "details": { ... }
}
```