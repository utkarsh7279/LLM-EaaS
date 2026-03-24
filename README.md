# LLM Evaluation-as-a-Service (EaaS)

🚀 **Production-style, rubric-driven evaluation platform for LLM outputs.**

A complete system for running rigorous LLM evaluations with regression detection, CI/CD gates, and enterprise-grade monitoring.

---

## ⚡ Quick Start (5 minutes)

### 1) Start Services

```bash
docker compose up -d
```

### 2) Initialize Database

```bash
psql postgresql://postgres:postgres@localhost:5433/llm_eaas -f backend/db/schema.sql
```

### 3) Configure Environment

**Backend** (`backend/.env`):
```bash
cp backend/.env.example backend/.env
```

**Frontend** (`frontend/.env.local`):
```bash
cp frontend/.env.example frontend/.env.local
```

### 4) Start Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5) Start Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 6) Test with Sample Data

```bash
# Upload the included sample dataset
# Then run evaluation with default rubric
```

---

## 📚 Documentation

**👉 [Start with Documentation Index →](DOCUMENTATION_INDEX.md)**

| Document | Purpose |
|----------|---------|
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | Navigation guide for all docs |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete API reference with examples |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Local, Docker, AWS, GCP, Azure deployment |
| [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) | Deployment-day checklist and smoke tests |
| [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) | All environment variables & settings |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues & solutions |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Quick lookup card |
| [PROJECT_DELIVERY_REPORT.md](PROJECT_DELIVERY_REPORT.md) | Delivery status & next steps |

---

## 🎯 Core Features

✅ **Dataset Management**
- Upload CSV (prompt, model_output, reference_output)
- Automatic validation & parsing
- Support for large datasets

✅ **Rubric-Driven Evaluation**
- Define custom numeric (0-5) and binary (pass/fail) rubrics
- LLM-as-judge with configurable temperature
- Automatic JSON parsing with fallback recovery
- Retry logic for failed evaluations (2 retries by default)

✅ **Experiment Tracking**
- Full experiment lifecycle (created → uploaded → running → completed)
- Per-item evaluation results with reasoning
- Aggregate metrics (mean, std_dev, safety_fail_rate)

✅ **Regression Detection**  
- Automatic comparison with baseline
- Configurable threshold (default 5%)
- Deployment gate support

✅ **Dual LLM Support**
- **Ollama** (local, free, privacy-friendly)
- **OpenAI** (production-ready, powerful models)

---

## 🏗️ Architecture

```
Frontend (Next.js)
       ↓
API Gateway (FastAPI)
       ↓
Service Layer (Experiment, Evaluation, Agent)
       ↓
Database (PostgreSQL + pgvector)
       ↓
LLM Provider (Ollama or OpenAI)
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, asyncio |
| Frontend | Next.js 14, React 18, TypeScript |
| Database | PostgreSQL 16 + pgvector |
| LLM | Ollama or OpenAI API |
| Deployment | Docker, Docker Compose |

---

## 📊 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/experiments/upload` | Create experiment from CSV |
| `POST` | `/experiments/run` | Run evaluation with rubric |
| `GET` | `/experiments/{id}` | Fetch results & metrics |
| `GET` | `/experiments/compare` | Compare two experiments |
| `GET` | `/experiments/{id}/ci-gate` | Deployment decision |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed examples.

---

## 🔧 Configuration

### Backend Environment Variables

```dotenv
# Required
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/llm_eaas

# LLM Provider (choose one)
LLM_EAAS_LLM_PROVIDER=ollama  # or "openai"
LLM_EAAS_LLM_MODEL=llama3.2   # or gpt-4-mini for OpenAI
LLM_EAAS_LLM_BASE_URL=http://localhost:11434/v1

# Optional
LLM_EAAS_REGRESSION_THRESHOLD=0.05      # 5% drop = regression
LLM_EAAS_JUDGE_TEMPERATURE_DEFAULT=0.2  # Lower = more consistent
LLM_EAAS_MAX_JUDGE_RETRIES=2
LLM_EAAS_ALLOWED_ORIGINS=["http://localhost:3000"]
LLM_EAAS_BASELINE_EXPERIMENT_ID=your-uuid-here
```

See [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for all options.

---

## 📦 Deployment

### Local Development
```bash
# Clone and setup (see Quick Start above)
```

### Docker Compose
```bash
docker compose up -d
```

### AWS ECS/Fargate
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:
- RDS PostgreSQL setup
- ECR image registry
- ECS task definitions
- Load balancing

### GCP Cloud Run
```bash
gcloud run deploy llm-eaas-backend \
  --image gcr.io/PROJECT/llm-eaas-backend:latest
```

### Azure App Service
```bash
az webapp create \
  --resource-group llm-eaas-rg \
  --plan llm-eaas-plan \
  --name llm-eaas-backend
```

---

## 🧪 Testing

```bash
# Backend unit tests
cd backend
source venv/bin/activate
python -m pytest tests/ -v

# Results:
# test_evaluation_agent.py::test_evaluation_agent_parses_json PASSED
# test_evaluation_agent.py::test_evaluation_agent_salvages_json PASSED
# test_metrics.py::test_detect_regression_flags_drop PASSED
# test_metrics.py::test_detect_regression_no_drop PASSED
# ====== 4 passed in 0.37s ======
```

---

## 📋 Sample Data

A sample CSV dataset with 10 evaluation items is included:

```bash
# Location: sample_data.csv
# Columns: prompt, model_output, reference_output
# Use to test the full evaluation workflow
```

---

## 🚨 Troubleshooting

**Database connection failed?**
```bash
docker compose ps postgres  # Verify running
psql postgresql://postgres:postgres@localhost:5433/llm_eaas -c "SELECT 1"
```

**LLM not responding?**
```bash
# Ollama
ollama serve

# OpenAI
# Verify API key in .env
```

**Frontend can't reach API?**
```bash
# Check NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
# Check backend ALLOWED_ORIGINS includes frontend URL
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues.

---

## 📈 Production Checklist

- [ ] Database backups configured
- [ ] HTTPS/TLS enabled
- [ ] Secrets in managed service (AWS Secrets Manager, etc.)
- [ ] Monitoring & logging set up
- [ ] Auto-scaling configured
- [ ] CI/CD pipeline deployed
- [ ] Health checks configured
- [ ] Firewall rules restricted

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete checklist.

---

## 🤝 Key Features

| Feature | Details |
|---------|---------|
| **Rubric Flexibility** | Numeric scales (e.g., 0-5) and binary (pass/fail) in single rubric |
| **Regression Detection** | Automatic comparison with baseline; configurable threshold |
| **CI/CD Integration** | Deploy gate endpoint for pipeline automation |
| **Multi-Provider LLM** | Switch between Ollama & OpenAI without code changes |
| **Robust Evaluation** | Auto-recovery from JSON parsing failures with retry logic |
| **Async Architecture** | Non-blocking I/O for large batch evaluations |
| **Type Safety** | Full TypeScript & Python type hints |
| **Enterprise Features** | Health checks, monitoring hooks, CORS, structured logging |

---

## 📊 Metrics Explained

- **Mean Score**: Average evaluation score across all items
- **Standard Deviation**: Spread of scores (lower = more consistent)
- **Safety Fail Rate**: Percentage of items that failed safety checks
- **Regression**: Detected when score drop exceeds threshold (default 5%)

---

## 🔐 Security

- **No hardcoded secrets** - Use environment variables
- **Database encryption** - Supported by cloud providers
- **CORS protected** - Whitelist allowed origins
- **Input validation** - CSV headers & rubric structure checked
- **SQL injection safe** - Uses parameterized queries (SQLAlchemy ORM)
- **Rate limiting** - Configure at reverse proxy level

---

## 📞 Support Resources

1. **API Reference** → [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Deployment Help** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
3. **Configuration Issues** → [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)
4. **Something Broken?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📄 License

This project is part of the LLM EaaS platform.

## 🎯 Next Steps

1. ✅ Start services (`docker compose up -d`)
2. ✅ Initialize database (schema.sql)
3. ✅ Configure environment (.env files)
4. ✅ Upload sample_data.csv via web UI
5. ✅ Run evaluation with default rubric
6. ✅ View results and metrics
7. → Deploy to staging/production (see DEPLOYMENT_GUIDE.md)
