# Quick Reference Card

## 🚀 Start Services (Local)
```bash
docker compose up -d              # Start PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -f backend/db/schema.sql
cd backend && source venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## 📁 Project Structure
```
llm-eaas/
├── backend/          → FastAPI server
│   ├── app/
│   │   ├── main.py              (entrypoint)
│   │   ├── routers/             (API routes)
│   │   ├── services/            (business logic)
│   │   ├── clients/             (LLM client)
│   │   ├── models/              (ORM & schemas)
│   │   ├── core/                (config)
│   │   ├── db/                  (database)
│   │   └── utils/               (helpers)
│   ├── tests/                   (unit tests)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         → Next.js UI
│   ├── app/
│   │   ├── page.tsx             (main UI)
│   │   ├── layout.tsx           (root layout)
│   │   └── globals.css          (styling)
│   ├── lib/api.ts               (API client)
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── sample_data.csv
└── docs/
    ├── README.md
    ├── API_DOCUMENTATION.md
    ├── DEPLOYMENT_GUIDE.md
    ├── CONFIGURATION_REFERENCE.md
    └── TROUBLESHOOTING.md
```

## 🔧 Key Endpoints

| Request | Endpoint | Purpose |
|---------|----------|---------|
| GET | `/health` | Health check |
| POST | `/experiments/upload` | Create experiment |
| POST | `/experiments/run` | Run evaluation |
| GET | `/experiments/{id}` | Get results |
| GET | `/experiments/compare?baseline=X&candidate=Y` | Compare experiments |
| GET | `/experiments/{id}/ci-gate` | Check deployment gate |

## ⚙️ Essential Configuration

### Backend (.env)
```dotenv
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/llm_eaas
LLM_EAAS_LLM_PROVIDER=ollama
LLM_EAAS_LLM_MODEL=llama3.2
LLM_EAAS_LLM_BASE_URL=http://localhost:11434/v1
LLM_EAAS_ALLOWED_ORIGINS=["http://localhost:3000"]
LLM_EAAS_REGRESSION_THRESHOLD=0.05
```

### Frontend (.env.local)
```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🧪 Test Commands

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# API health check
curl http://localhost:8000/health

# Sample upload
curl -X POST -F "file=@sample_data.csv" http://localhost:8000/experiments/upload

# View logs
docker compose logs -f backend
```

## 📊 Sample Rubric
```json
{
  "factuality": { "min": 0, "max": 5 },
  "relevance": { "min": 0, "max": 5 },
  "clarity": { "min": 0, "max": 5 },
  "safety": { "type": "pass_fail" }
}
```

## 🐛 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Database connection fail | `docker compose ps postgres` |
| LLM not responding | Ollama: `ollama serve` \| OpenAI: Check API key |
| Frontend can't reach API | Check `NEXT_PUBLIC_API_BASE_URL` |
| Port already in use | `lsof -i :8000` then `kill -9 <PID>` |
| Container keeps restarting | `docker compose logs backend` |

## 📚 Documentation Links

- **Quick Start**: [README.md](README.md)
- **API Endpoints**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Deploy Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Configuration**: [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)
- **Issues & Fixes**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🔄 Workflow Example

```bash
# 1. Upload dataset
RESPONSE=$(curl -X POST -F "file=@sample_data.csv" \
  http://localhost:8000/experiments/upload)
EXPERIMENT_ID=$(echo $RESPONSE | jq -r '.experiment_id')

# 2. Run evaluation
curl -X POST http://localhost:8000/experiments/run \
  -H "Content-Type: application/json" \
  -d "{
    \"experiment_id\": \"$EXPERIMENT_ID\",
    \"rubric\": {
      \"factuality\": {\"min\": 0, \"max\": 5},
      \"relevance\": {\"min\": 0, \"max\": 5},
      \"safety\": {\"type\": \"pass_fail\"}
    }
  }"

# 3. Get results
curl http://localhost:8000/experiments/$EXPERIMENT_ID

# 4. Compare with baseline
curl "http://localhost:8000/experiments/compare?baseline=baseline-uuid&candidate=$EXPERIMENT_ID"

# 5. Check CI gate
curl http://localhost:8000/experiments/$EXPERIMENT_ID/ci-gate
```

## 🐳 Docker Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f [service]

# Rebuild images
docker compose build --no-cache

# Remove volumes (caution!)
docker compose down -v

# Scale service
docker compose up -d --scale backend=3
```

## 📱 Frontend Features

- ✅ Dataset upload (drag & drop)
- ✅ CSV validation
- ✅ Experiment management
- ✅ Rubric editor
- ✅ Results table with per-row details
- ✅ Comparison tool
- ✅ CI gate checker
- ✅ JSON export

## 🎯 Environment Variables By Type

**Databases**:
- `LLM_EAAS_DATABASE_URL` (required)

**LLM Provider**:
- `LLM_EAAS_LLM_PROVIDER` (ollama | openai)
- `LLM_EAAS_LLM_MODEL`
- `LLM_EAAS_LLM_BASE_URL`
- `LLM_EAAS_OPENAI_API_KEY`

**Evaluation**:
- `LLM_EAAS_JUDGE_TEMPERATURE_DEFAULT` (0.0-1.0)
- `LLM_EAAS_MAX_JUDGE_RETRIES`
- `LLM_EAAS_REGRESSION_THRESHOLD` (0.0-1.0)

**Baseline**:
- `LLM_EAAS_BASELINE_EXPERIMENT_ID` (optional UUID)

**CORS**:
- `LLM_EAAS_ALLOWED_ORIGINS` (JSON list)

## 🚀 Deployment Quick Links

- **Local**: Run services locally, see [README.md](README.md)
- **Docker**: Use docker-compose.yml, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#docker-deployment)
- **AWS**: ECS/RDS, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#aws-deployment)
- **GCP**: Cloud Run/SQL, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#gcp-deployment)
- **Azure**: App Service/Database, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#azure-deployment)

## ✅ Pre-Deployment Checklist

- [ ] Postgres running and initialized
- [ ] Backend .env configured
- [ ] Frontend .env.local configured
- [ ] LLM service running (Ollama or OpenAI key set)
- [ ] API health check passes (`curl /health`)
- [ ] Frontend loads (`http://localhost:3000`)
- [ ] Can upload sample_data.csv
- [ ] Can run evaluation
- [ ] Unit tests pass (`pytest tests/`)
- [ ] No errors in logs

## 🔐 Security Checklist

- [ ] Never commit .env files
- [ ] Use strong database password
- [ ] Set ALLOWED_ORIGINS to specific domains
- [ ] Enable HTTPS in production
- [ ] Restrict database access via firewall
- [ ] Use managed secrets service (AWS Secrets Manager, etc.)
- [ ] Implement rate limiting
- [ ] Enable database encryption
- [ ] Configure backup strategy
- [ ] Monitor access logs

## 📞 Support Matrix

| Issue | Consult |
|-------|---------|
| "How do I use the API?" | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) |
| "How do I deploy?" | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| "What env vars do I need?" | [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) |
| "Something's broken" | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| "What's in this project?" | [DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md) |

## 🎯 Next Steps

1. **Start**: Run `docker compose up -d`
2. **Initialize**: Load schema with `psql -f backend/db/schema.sql`
3. **Configure**: Set up .env files
4. **Test**: Upload sample_data.csv and run evaluation
5. **Deploy**: Choose platform and follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
6. **Monitor**: Set up logging and health checks
7. **Maintain**: Follow backup and scaling guidelines

---

**Last Updated**: February 19, 2026  
**Project Status**: ✅ Production Ready
