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

### Local Development
```bash
python3 app.py
```

The application will start on `http://localhost:5000` with debug mode enabled.

### Production (Render)
The application is configured to run on Render with the following files:
- `Procfile` - Defines the web process
- `requirements.txt` - Python dependencies including Gunicorn
- `runtime.txt` - Python version specification
- `render.yaml` - Render deployment configuration
- `wsgi.py` - WSGI entry point

### Deploy to Render

#### Method 1: Using render.yaml (Recommended)
1. **Push your code to GitHub**
2. **Connect your repository to Render**
3. **Render will automatically detect the `render.yaml` file**
4. **The service and database will be created automatically**

#### Method 2: Manual Configuration
1. **Connect your GitHub repository to Render**
2. **Create a new Web Service** and select your repository
3. **Configure the service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** `Python 3`
4. **Add Environment Variables:**
   - `FLASK_ENV=production`
   - `DATABASE_URL` (will be provided by Render PostgreSQL addon)
5. **Deploy!**

#### Method 3: Using Docker
1. **Connect your GitHub repository to Render**
2. **Select "Docker" as the environment**
3. **Render will automatically use the Dockerfile**

### Environment Variables for Render
- `FLASK_ENV=production` - Sets Flask to production mode
- `DATABASE_URL` - Automatically provided by Render PostgreSQL addon
- `PORT` - Automatically set by Render (usually 10000)

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