# GRC AI — Compliance Intelligence Platform

An AI-powered Governance, Risk & Compliance (GRC) platform that automatically generates tailored compliance policies and procedures for organizations based on their industry, region, and selected regulatory frameworks.

---

## Features

- **Organization Profiling** — Describe your org in plain English; the AI agent detects your industry, region, and applicable frameworks automatically
- **Framework Matching** — Supports 10 major compliance frameworks: GDPR, HIPAA, ISO 27001, NIST CSF, PCI DSS, SOC 2, CCPA, DPDP, SOX, FedRAMP
- **Policy Generation** — AI-generated, framework-aligned policies (data protection, access control, incident response, and more)
- **Procedure Generation** — Step-by-step operational procedures tailored to your org context
- **Personalization** — Guided Q&A to customize documents to your specific setup
- **Export** — Download generated policies and procedures as `.docx` files
- **Authentication** — JWT-based auth with role-based access control (Admin / Compliance Officer)
- **Admin Panel** — User approval workflow, role management, and user oversight
- **History** — Browse previously generated sessions and regenerate documents

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM with SQLite
- [CrewAI](https://crewai.com/) — Multi-agent AI orchestration
- [Groq](https://groq.com/) — LLM inference (Llama 3.3 70B / Llama 3.1 8B)
- [Tavily](https://tavily.com/) — Web search for org profiling
- [python-docx](https://python-docx.readthedocs.io/) — Document export
- PyJWT + bcrypt — Authentication & security

**Frontend**
- [Next.js 16](https://nextjs.org/) (App Router) — React framework
- [Tailwind CSS v4](https://tailwindcss.com/) — Styling
- [Zustand](https://zustand-demo.pmnd.rs/) — State management
- [Axios](https://axios-http.com/) — HTTP client
- [Lucide React](https://lucide.dev/) — Icons

---

## Project Structure

```
.
├── backend/
│   ├── agents/             # CrewAI agents (org profiler, policy & procedure generators)
│   ├── config/             # Frameworks registry, LLM config, auth, dependencies
│   ├── db/                 # SQLAlchemy models, CRUD operations
│   ├── export/             # DOCX builder
│   ├── models/             # Pydantic schemas
│   ├── tests/              # Test suite
│   ├── main.py             # FastAPI application entry point
│   ├── requirements.txt
│   └── .env                # Backend environment variables (see setup below)
└── frontend/
    ├── app/                # Next.js App Router pages & components
    ├── api/                # API client functions
    ├── hooks/              # React hooks
    ├── store/              # Zustand stores
    ├── types/              # TypeScript types
    └── .env.local          # Frontend environment variables
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Groq API key](https://console.groq.com/) (free tier available)
- A [Tavily API key](https://tavily.com/) (free tier available)

---

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
# LLM
GROQ_API_KEY_1=your_groq_api_key

# Web search (for org profiling)
TAVILY_API_KEY=your_tavily_api_key

# Auth
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Start the backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: `http://10.4.32.170:8001/docs`

---

### Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://10.4.32.170:8001
```

Start the development server:

```bash
npm run dev
```

App available at: `http://localhost:3000`

---

## Default Accounts

On first startup the backend auto-creates two accounts:

| Role               | Email                        | Password     |
|--------------------|------------------------------|--------------|
| Admin              | admin@complianceiq.com       | Admin1234!   |
| Compliance Officer | demo@example.com             | Demo1234!    |

> **Change these credentials before deploying to production.**

---

## Supported Frameworks

| Framework   | Region         | Focus                                      |
|-------------|----------------|--------------------------------------------|
| GDPR        | EU / EEA       | Data protection & privacy                  |
| HIPAA       | United States  | Healthcare data (PHI)                      |
| ISO 27001   | International  | Information security management            |
| NIST CSF    | United States  | Cybersecurity framework                    |
| PCI DSS     | Global         | Payment card data security                 |
| SOC 2       | United States  | SaaS / cloud service trust criteria        |
| CCPA / CPRA | California, US | Consumer privacy rights                    |
| DPDP        | India          | Digital personal data protection           |
| SOX         | United States  | Financial reporting & corporate governance |
| FedRAMP     | United States  | Federal cloud security                     |

---

## API Overview

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| POST   | `/auth/signup`                  | Register new account               |
| POST   | `/auth/login`                   | Login and receive JWT tokens       |
| POST   | `/auth/refresh`                 | Refresh access token               |
| POST   | `/auth/logout`                  | Revoke session                     |
| GET    | `/frameworks`                   | List all supported frameworks      |
| POST   | `/profile`                      | Profile an organization with AI    |
| POST   | `/policies/generate`            | Generate compliance policies       |
| POST   | `/procedures/generate`          | Generate compliance procedures     |
| GET    | `/history`                      | List past sessions                 |
| POST   | `/export/docx`                  | Export session as DOCX             |
| GET    | `/admin/users`                  | List all users (admin only)        |
| POST   | `/admin/users/{id}/approve`     | Approve a pending user (admin only)|

Full interactive docs: `http://10.4.32.170:8001/docs`

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable                      | Description                              |
|-------------------------------|------------------------------------------|
| `GROQ_API_KEY_1` ... `_6`     | Groq API keys (supports multiple for rotation) |
| `TAVILY_API_KEY`              | Tavily search API key                    |
| `SECRET_KEY`                  | JWT signing secret                       |
| `JWT_ALGORITHM`               | JWT algorithm (default: HS256)           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default: 30)           |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token TTL (default: 7)           |

### Frontend (`frontend/.env.local`)

| Variable                  | Description                        |
|---------------------------|------------------------------------|
| `NEXT_PUBLIC_API_URL`     | Backend API base URL               |
| `NEXT_PUBLIC_API_TIMEOUT` | Request timeout in ms (default: 30000) |

---

## Branch Strategy

| Branch   | Purpose                              |
|----------|--------------------------------------|
| `master` | Stable production-ready code         |
| `alpha`  | Active development / feature preview |

---

## License

Private — all rights reserved.
