# 🚀 Billx-Agent

> **Version**: 3.12  
> **Framework**: FastAPI, PostgreSQL, Python  
> **Purpose**: API-as-a-service enabling users to query and manage their databases using natural language (text or voice) via integrated LLM and ElevenLabs services.

---

## 📘 1. Overview

**Billx-Agent** is an intelligent API gateway designed to connect with user databases and facilitate human-like querying using **natural language** or **voice commands**. It bridges voice/text input to SQL output through a seamless integration of AI models, speech technologies, and database drivers.

### 🔑 Key Features

- **Conversational SQL**: NLP-powered SQL generation from natural language prompts
- **Voice I/O**: STT (speech-to-text) and TTS (text-to-speech) using ElevenLabs
- **Database Linking**: Connect external databases securely via API
- **Usage Tracking**: Monitor API usage, quota consumption, and historical queries
- **Role-Based Access Control (RBAC)**: User permissions scoped to organizations and roles
- **Quota Purchase**: Credit-based quota management with payment gateway integration

---

## 🔌 2. API Endpoint Reference

All endpoints follow RESTful conventions and return standard HTTP response codes (`200 OK`, `401 Unauthorized`, `422 Validation Error`, etc.).

### 👥 Authentication & User Management

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/sign-up` | POST | Register new user | ❌ |
| `/sign-in` | POST | Login and receive JWT | ❌ |
| `/me` | GET | Retrieve current user details | ✅ |
| `/logout` | GET | Logout and blacklist token | ✅ |
| `/send-otp` | POST | Send OTP to email/phone | ❌ |
| `/password-reset/request` | POST | Start password reset flow | ❌ |
| `/users/{user_id}` | GET | Admin fetch user by ID | Admin |
| `/users/{user_id}/change-role/{new_role_id}` | POST | Promote/demote user | Super Admin |

### 🧠 Natural Language Query Engine

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query/chat` | POST | Send a text prompt to generate SQL |
| `/query/audio-chat` | POST | Send audio file to transcribe, query DB, and receive spoken answer |

**Example Request:**
```json
{
  "db_url": "postgresql://user:pass@host:5432/db",
  "prompt": "What were the top 3 selling products last month?"
}
```

### 🗣️ Voice Services (ElevenLabs)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stt` | POST | Convert uploaded speech (audio) into text |
| `/tts` | POST | Convert provided text into spoken audio |

### 🧾 Tool Templates (Query Builders)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools` | POST | Create reusable SQL tool via prompt |
| `/tools/{tool_id}/execute` | POST | Run tool with parameters (e.g. filters, date ranges) |

### 🔐 Roles & Permissions

| Endpoint | Method | Description | Access |
|----------|--------|-------------|--------|
| `/roles` | POST | Create new role | Super Admin |
| `/roles/{role_id}` | PUT | Update role’s access rules | Super Admin |

### 💳 Quotas & Payments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/quota/usage` | GET | View user’s current quota and usage |
| `/payment` | POST | Purchase additional quota or subscription |

---

## 🔁 3. Voice Query Flow (Diagram)

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant ElevenLabs
    participant LLM
    participant DB

    Client->>API: POST /audio-chat (audio file)
    API->>ElevenLabs: Convert speech to text
    ElevenLabs-->>API: Transcript
    API->>LLM: Generate SQL query from transcript
    LLM-->>API: SQL statement
    API->>DB: Execute SQL
    DB-->>API: Query result
    API->>ElevenLabs: Convert result to speech
    ElevenLabs-->>API: Audio file
    API-->>Client: Audio response
```

---

## 📦 4. Core Modules (Code Reference)

### `ai_sql_agent.py`

- Handles the core logic for translating prompts into SQL
- Cleans, validates, and executes SQL on connected DB
- Tracks OpenAI token usage for quota deduction

### `tool_controller.py`

- Manages parameterized SQL templates created via prompt
- Supports reusability and safe SQL generation
- Exposes `POST /tools` and `/tools/{tool_id}/execute`

### `users.py`, `roles.py`, `user_database.py`

- Defines SQLAlchemy models for:
  - `User`
  - `Role`
  - `Organization`
  - `UserDatabase`
- Manages JWT auth and scoped role-based access

### `api_usage.py`, `payment.py`

- Monitors API activity (monthly quota, usage logs)
- Implements purchase flow and logs transactions

### `tool.py`

- Interfaces with **ElevenLabs API** for:
  - Speech-to-text
  - Text-to-speech
- Records tool usage and cost impact

---

## ☁️ 5. Deployment Guide

### Recommended Stack

| Component | Service | Details |
|----------|---------|---------|
| API Hosting | Render / Railway / AWS EC2 | FastAPI + Uvicorn |
| DB | AWS RDS / Supabase | PostgreSQL 13+ |
| Speech | [ElevenLabs](https://www.elevenlabs.io) | Free + Paid plans |
| Auth | JWT + Redis | Token revocation via cache |
| Monitoring | Prometheus + Grafana | Optional but recommended |

### Docker Setup

```bash
docker build -t billx-agent .
docker run -p 8000:8000 --env-file .env billx-agent
```

### Monitoring

```yaml
# prometheus.yaml
scrape_configs:
  - job_name: 'billx_agent'
    static_configs:
      - targets: ['localhost:8000']
```

---

## ✅ 6. Testing Strategy

- **Framework**: `pytest`, `httpx`, `pytest-cov`
- **Coverage**: `pytest --cov=.` (target >90%)
- **Mocking**: ElevenLabs and OpenAI APIs mocked using `unittest.mock`
- **CI/CD**: GitHub Actions pipeline:
  - Lint check (ruff)
  - Unit + integration tests
  - Docker build and push

---

## 📈 7. Changelog

### v3.12

- 🧠 Integrated LLM for text-to-SQL conversion
- 🗣️ Added ElevenLabs STT + TTS support
- 🔐 Role-based access control (RBAC)
- 🧾 Introduced usage tracking and billing
- 💳 Enabled quota purchases and payments
- 🧪 100% coverage on core API logic

---

## 🧰 8. Documentation Access

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: `/openapi.json`
- **Postman Collection**: _[Available on request]_

---

### Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [OpenAI](https://openai.com/)
- [ElevenLabs](https://www.elevenlabs.io/)