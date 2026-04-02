# Free-Tier Deployment Guide

This guide deploys LLM EaaS with zero required monthly spend.

## Target Setup
- Backend: Render Web Service (free tier)
- Database: Render PostgreSQL (free tier)
- Frontend: Vercel (free tier)
- LLM Provider: Groq free tier (OpenAI-compatible endpoint)

## Prerequisites
- GitHub repo connected
- Render account
- Vercel account
- Groq API key

## Step 1: Create Groq API Key
1. Open https://console.groq.com.
2. Create an API key.
3. Save the key securely.

## Step 2: Provision Render PostgreSQL
1. Render Dashboard -> New -> PostgreSQL.
2. Choose free tier and region.
3. Copy Internal Database URL and External Database URL.
4. Convert Internal URL prefix from postgres:// to postgresql+asyncpg:// for app config.

## Step 3: Deploy Backend on Render
1. Render Dashboard -> New -> Web Service.
2. Select repository and branch main.
3. Set root directory to backend.
4. Select Python runtime.
5. Build command: pip install -r requirements.txt
6. Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

## Step 4: Backend Environment Variables
Required values:
- LLM_EAAS_DATABASE_URL=<converted internal DB URL>
- LLM_EAAS_ALLOWED_ORIGINS=["*"]
- LLM_EAAS_LLM_PROVIDER=openai
- LLM_EAAS_LLM_BASE_URL=https://api.groq.com/openai/v1
- LLM_EAAS_LLM_MODEL=mixtral-8x7b-32768
- LLM_EAAS_LLM_API_KEY=<your_groq_key>
- LLM_EAAS_LLM_TIMEOUT_SECONDS=120
- LLM_EAAS_ENVIRONMENT=production

## Step 5: Initialize Database Schema
Run locally:

psql "<external_database_url>" -f backend/db/schema.sql

## Step 6: Validate Backend
- Check health endpoint: /health
- Confirm logs show startup success and DB connectivity

## Step 7: Deploy Frontend on Vercel
1. Import repo in Vercel.
2. Set root directory to frontend.
3. Add env variable:
   - NEXT_PUBLIC_API_BASE_URL=https://<render-backend-domain>
4. Deploy.

## Step 8: Smoke Test
1. Open frontend URL.
2. Upload sample CSV.
3. Run one evaluation.
4. Confirm no API/CORS errors.

## Recommended Hardening After First Successful Deploy
- Replace allowed origins wildcard with exact frontend domain.
- Add provider usage monitoring (Groq dashboard).
- Add periodic health checks and alerting.
