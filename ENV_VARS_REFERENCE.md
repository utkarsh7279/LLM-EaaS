# Environment Variables Reference - FREE TIER (Local Only)

**Do NOT commit this file. Use it as a local reference for Render setup.**

**Using Groq (FREE LLM) - No OpenAI needed!**

---

## What You Need BEFORE Starting Render Setup

### 1. Groq API Key (FREE)
- Go to: https://console.groq.com
- Sign up with GitHub or email (no credit card)
- Go to **API Keys** section
- Click **Create API Key**
- Copy the key (starts with `gsk_`)
- Example: `gsk_abc123xyz...`
- **Free tier: 10,000 requests/day** (perfect for testing)

### 2. Render PostgreSQL Internal Database URL
- Create database in Render (Step 2 of checklist)
- Copy Internal Database URL
- Transform it: change `postgres://` to `postgresql+asyncpg://`
- Example:
  ```
  postgresql+asyncpg://default:password123@ep-xyz-internal.postgres.onrender.com:5432/llm_eaas
  ```

---

## Environment Variables to Paste in Render Backend Service

Copy each block below ONE AT A TIME into Render:

```
### Variable 1
Key: LLM_EAAS_DATABASE_URL
Value: postgresql+asyncpg://USER:PASSWORD@HOSTNAME:5432/DBNAME
(from Render PostgreSQL Internal URL, with postgres:// → postgresql+asyncpg://)
```

```
### Variable 2
Key: LLM_EAAS_ALLOWED_ORIGINS
Value: ["*"]
```

```
### Variable 3
Key: LLM_EAAS_LLM_PROVIDER
Value: groq
(Groq is OpenAI-compatible, but we now name the provider explicitly as "groq")
```

```
### Variable 4
Key: LLM_EAAS_LLM_BASE_URL
Value: https://api.groq.com/openai/v1
(Groq's OpenAI-compatible endpoint)
```

```
### Variable 5
Key: LLM_EAAS_LLM_MODEL
Value: mixtral-8x7b-32768
(Groq's free powerful model)
```

```
### Variable 6
Key: LLM_EAAS_LLM_API_KEY
Value: gsk_xxxxx...
(your Groq API key from https://console.groq.com)
```

```
### Variable 7
Key: LLM_EAAS_LLM_TIMEOUT_SECONDS
Value: 120
```

```
### Variable 8
Key: LLM_EAAS_ENVIRONMENT
Value: production
```

---

## After Database Schema is Loaded

Frontend environment variable for Vercel:

```
Key: NEXT_PUBLIC_API_BASE_URL
Value: https://llm-eaas-backend.onrender.com
(your Render backend service URL)
```

---

## Local Terminal Command for Schema

Run this ONCE after backend is live:

```bash
psql "postgresql://USER:PASSWORD@EXTERNAL-HOST:5432/dbname" -f backend/db/schema.sql
```

Get the External Database URL from Render PostgreSQL details page.

---

## All Config Values in One Place (for reference)

```json
{
  "database_url": "postgresql+asyncpg://...",
  "allowed_origins": ["*"],
  "llm_provider": "openai",
  "llm_base_url": "https://api.groq.com/openai/v1",
  "llm_model": "mixtral-8x7b-32768",
  "llm_api_key": "gsk_...",
  "llm_timeout_seconds": 120,
  "environment": "production"
}
```

---

**Remember:** This file is local only. Remove it after deployment if you want.

**Cost: $0 - Using Groq free tier (10,000 req/day)**
