# Hospital Billing System

A full-stack, production-ready multi-tenant hospital/clinic billing system.

## 🏗️ Architecture

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + Vite + Tailwind CSS v3 |
| **Backend** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 15+ |
| **Auth** | JWT (access + refresh tokens) |
| **PDF** | ReportLab |
| **Email** | aiosmtplib |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb hospital_billing
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment config
copy .env.example .env
# Edit .env with your database URL and settings

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## 📋 Features

### Multi-Tenant Architecture
- Each clinic/hospital operates in isolated data space
- Tenant ID enforcement on all database queries
- Role-based access control (Admin / Staff)

### Modules
1. **Patient Management** — CRUD, search, filter by gender
2. **Doctor Management** — Specializations, consultation fees, availability
3. **Test & MRP Management** — Categories, dynamic pricing per clinic
4. **Billing System** — Auto-calculations, tax (18% GST), discounts
5. **Receipt Branding** — Clinic logo, name, address on PDF receipts
6. **Account Management** — Registration, JWT login, staff management
7. **Dashboard** — Revenue analytics, charts, recent transactions
8. **Reports** — CSV export with date and status filters

### Billing Features
- Unique bill number format: `INV-YYYYMMDD-XXXX`
- Auto-calculate subtotal, tax (18% GST), discounts
- Multiple payment modes (Cash, Card, UPI, Online)
- PDF receipt download with clinic branding
- Email receipt to patient with PDF attachment

## 🔑 API Endpoints

| Module | Endpoints |
|--------|-----------|
| **Auth** | `POST /register`, `POST /login`, `POST /refresh`, `GET /me` |
| **Patients** | `GET`, `POST`, `PUT`, `DELETE /patients` |
| **Doctors** | `GET`, `POST`, `PUT`, `DELETE /doctors` |
| **Tests** | `GET`, `POST`, `PUT`, `DELETE /tests` + `/categories` |
| **Bills** | `GET`, `POST`, `PUT`, `DELETE /bills` + `/pdf`, `/send-email` |
| **Clinic** | `GET`, `PUT /clinic` + `POST /clinic/logo` |
| **Dashboard** | `GET /dashboard/stats`, `/chart-data`, `/recent` |
| **Users** | `GET`, `POST`, `PUT`, `DELETE /users` |
| **Reports** | `GET /reports/export/csv` |

All endpoints are prefixed with `/api/v1/`.

## 🏥 Environment Variables

See `backend/.env.example` for all configurable settings:
- Database connection
- JWT secret and expiry
- CORS origins
- SMTP email configuration
- File upload limits
- Default tax rate and currency

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers
│   │   ├── core/            # Config, security, deps
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI entry point
│   ├── uploads/             # Logos & PDFs
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/      # Reusable UI
    │   ├── layouts/         # Layout wrappers
    │   ├── pages/           # Page components
    │   ├── services/        # API client
    │   └── store/           # Zustand state
    └── package.json
```

## 🛡️ Security

- Bcrypt password hashing
- JWT access tokens (30 min) + refresh tokens (7 days)
- Tenant isolation on every database query
- Role-based access control (admin/staff)
- File upload validation (type + size)
- CORS configuration
- Global exception handling

## 📦 Deployment

### Render / Railway
1. Set environment variables from `.env.example`
2. Backend: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Frontend: `npm run build` → serve `dist/` folder

### Docker (Coming Soon)
Docker Compose configuration for local development and deployment.

## 📄 License

MIT
