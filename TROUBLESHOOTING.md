# Troubleshooting Guide

## Quick Diagnosis

### System Health Check
```bash
# 1. Check all services are running
docker compose ps

# 2. Check API health
curl http://localhost:8000/health

# 3. Check database connection
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -c "SELECT 1"

# 4. Check frontend is accessible
curl http://localhost:3000

# 5. View logs
docker compose logs --tail=50
```

---

## Common Issues

### 1. Database Connection Issues

#### Problem: "Could not connect to database"

**Symptoms**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solutions**:

**Check PostgreSQL is running**:
```bash
# Docker Compose
docker compose ps postgres
# Should show "Up" status

# If not running
docker compose up -d postgres
```

**Verify connection string**:
```bash
# Check .env file
cat backend/.env | grep DATABASE_URL

# Test connection manually
psql postgresql://postgres:postgres@localhost:5432/llm_eaas

# If connection refused, check port
# Docker maps 5433 → 5432
# Use 5433 for local connection, 5432 for docker-to-docker
```

**Check database exists**:
```bash
# List databases
psql postgresql://postgres:postgres@localhost:5432/postgres -c "\l"

# Create if missing
psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE DATABASE llm_eaas"

# Apply schema
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -f backend/db/schema.sql
```

---

#### Problem: "SSL connection has been closed unexpectedly"

**Solution**:
```dotenv
# Add sslmode=disable for local development
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/llm_eaas?ssl=false
```

---

### 2. LLM Provider Issues

#### Problem: "Could not connect to LLM service"

**For Ollama**:

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not responding, start Ollama
ollama serve

# Check model is pulled
ollama list
# If llama3.2 not in list:
ollama pull llama3.2

# Test generation
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

**For OpenAI**:

```bash
# Check API key is valid
export OPENAI_API_KEY="sk-your-key"
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check .env has correct key
cat backend/.env | grep OPENAI_API_KEY
```

---

#### Problem: "LLM returned invalid JSON"

**Symptoms**:
```
ValueError: LLM judge failed to return valid JSON after retries
```

**Causes & Solutions**:

1. **Temperature too high**: Lower temperature to 0.2-0.3
2. **Complex rubric**: Simplify rubric definition
3. **Model struggles with JSON**: Use OpenAI with `response_format=json_object`

**Test evaluation manually**:
```bash
# Upload dataset
EXPERIMENT_ID=$(curl -X POST -F "file=@sample_data.csv" http://localhost:8000/experiments/upload | jq -r '.experiment_id')

# Run with logging
curl -X POST http://localhost:8000/experiments/run \
  -H "Content-Type: application/json" \
  -d "{
    \"experiment_id\": \"$EXPERIMENT_ID\",
    \"rubric\": {
      \"factuality\": {\"min\": 0, \"max\": 5}
    },
    \"temperature\": 0.2
  }"

# Check backend logs for LLM response
docker compose logs backend | grep -A 20 "LLM"
```

---

### 3. Frontend Issues

#### Problem: "API calls failing from frontend"

**Symptoms**: Network errors in browser console

**Solutions**:

**Check API URL**:
```bash
# Verify frontend .env.local
cat frontend/.env.local

# Should be:
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Rebuild frontend if changed
cd frontend
npm run build
npm run dev
```

**Check CORS**:
```bash
# Backend .env should include frontend URL
LLM_EAAS_ALLOWED_ORIGINS=["http://localhost:3000"]

# Restart backend after changing
docker compose restart backend
```

**Test API from browser console**:
```javascript
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

---

#### Problem: "CSV upload validation fails"

**Symptoms**: "Missing required columns: prompt, model_output"

**Solution**:
```csv
# Ensure CSV has correct headers (first line):
prompt,model_output,reference_output
"Your prompt here","Model response","Expected output"

# Common issues:
# - Extra quotes: prompt should be prompt not "prompt"
# - Extra spaces: prompt, not prompt 
# - Wrong column names: Prompt vs prompt (case matters)
```

---

### 4. Performance Issues

#### Problem: Evaluation is very slow

**Diagnosis**:
```bash
# Check how long each item takes
docker compose logs backend | grep "Evaluating item"

# If taking >30 seconds per item:
```

**Solutions**:

1. **Check LLM service latency**:
```bash
# Time a simple request
time curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "messages": [{"role": "user", "content": "hi"}]}'
```

2. **Reduce timeout**:
```dotenv
LLM_EAAS_LLM_TIMEOUT_SECONDS=30
```

3. **Use faster model**:
```dotenv
# Switch from llama3.2 to smaller model
LLM_EAAS_LLM_MODEL=llama2

# Or use OpenAI
LLM_EAAS_LLM_PROVIDER=openai
LLM_EAAS_LLM_MODEL=gpt-4-mini
```

---

#### Problem: Database queries are slow

**Diagnosis**:
```sql
-- Check for missing indexes
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public';

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM evaluation_results WHERE experiment_id = 'some-uuid';
```

**Solutions**:
```sql
-- Rebuild indexes
REINDEX DATABASE llm_eaas;

-- Vacuum database
VACUUM ANALYZE;
```

---

### 5. Docker Issues

#### Problem: "Port already in use"

**Symptoms**:
```
Error: bind: address already in use
```

**Solutions**:
```bash
# Find what's using the port
lsof -i :8000
lsof -i :3000
lsof -i :5433

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Changed from 8000:8000
```

---

#### Problem: "Container keeps restarting"

**Diagnosis**:
```bash
# Check logs
docker compose logs backend

# Check container status
docker compose ps
```

**Common causes**:
- Missing environment variables
- Database not ready
- Invalid configuration
- Missing dependencies

**Solution**:
```bash
# Remove containers and rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

### 6. API Errors

#### Problem: "Experiment not found"

**Check experiment exists**:
```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/llm_eaas

# List experiments
SELECT id, status, created_at FROM experiments ORDER BY created_at DESC LIMIT 10;

# Check specific experiment
SELECT * FROM experiments WHERE id = 'your-experiment-uuid';
```

---

#### Problem: "Baseline experiment not configured"

**Symptoms**:
```
ValueError: Baseline experiment not configured
```

**Solutions**:

**Option 1: Set baseline in .env**:
```dotenv
LLM_EAAS_BASELINE_EXPERIMENT_ID=your-baseline-uuid
```

**Option 2: Mark experiment as baseline in DB**:
```sql
UPDATE experiments 
SET is_baseline = true 
WHERE id = 'your-experiment-uuid';
```

---

### 7. Data Issues

#### Problem: "No items found for experiment"

**Check items exist**:
```sql
-- Connect to DB
psql postgresql://postgres:postgres@localhost:5432/llm_eaas

-- Check items
SELECT COUNT(*) FROM evaluation_items WHERE experiment_id = 'your-uuid';

-- If 0, re-upload the dataset
```

---

#### Problem: "Safety fail rate is wrong"

**Expected behavior**:
- Safety field must be `"pass"` or `"fail"` (string)
- Boolean values are auto-converted: `true` → `"pass"`, `false` → `"fail"`

**Check rubric scores**:
```sql
SELECT rubric_scores->'safety' as safety, COUNT(*) 
FROM evaluation_results 
WHERE experiment_id = 'your-uuid'
GROUP BY rubric_scores->'safety';
```

---

### 8. Testing Issues

#### Problem: Tests fail with database connection error

**Solution**:
```bash
# Tests use stub client, shouldn't connect to DB
# If failing, check import paths

cd backend
python -m pytest tests/ -v

# If still failing, check test file
cat tests/test_evaluation_agent.py
```

---

## Debugging Techniques

### Enable SQL Logging

```python
# In app/db/session.py, temporarily add:
async_engine = create_async_engine(
    settings.database_url, 
    pool_pre_ping=True,
    echo=True  # <-- Add this line
)
```

### Enable Detailed Logging

```python
# In app/utils/logging.py
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
```

### Test LLM Directly

```python
# Create test script: test_llm.py
from app.clients.openai_client import OpenAIClient

client = OpenAIClient()
response = client.generate_judge_response(
    system_prompt="You are a helpful assistant. Return JSON only.",
    user_prompt='{"test": "respond with valid JSON"}',
    temperature=0.2
)
print(response)
```

```bash
cd backend
source venv/bin/activate
python test_llm.py
```

---

## Emergency Recovery

### Reset Everything

```bash
# ⚠️ WARNING: This deletes all data

# Stop and remove containers
docker compose down -v

# Remove database volume
docker volume rm "llm eaas_pgdata"

# Rebuild and restart
docker compose build --no-cache
docker compose up -d

# Re-initialize database
psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE DATABASE llm_eaas"
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -f backend/db/schema.sql
```

### Backup Before Reset

```bash
# Backup database
pg_dump postgresql://postgres:postgres@localhost:5432/llm_eaas > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore later
psql postgresql://postgres:postgres@localhost:5432/llm_eaas < backup_20260219_123456.sql
```

---

## Logging Best Practices

### View Logs by Service

```bash
# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend

# PostgreSQL only
docker compose logs -f postgres

# All services
docker compose logs -f
```

### Filter Logs

```bash
# Errors only
docker compose logs backend | grep ERROR

# Specific experiment
docker compose logs backend | grep "experiment-uuid"

# Last 1 hour
docker compose logs --since 1h
```

---

## Getting Help

### Information to Include

When reporting issues, include:

1. **Error message** (full traceback)
2. **Steps to reproduce**
3. **Environment** (OS, Docker version, Python version)
4. **Logs** (relevant portions)
5. **Configuration** (sanitized .env)

### Collect Debug Info

```bash
# System info
uname -a
docker --version
docker compose version
python3 --version

# Service status
docker compose ps

# Recent logs
docker compose logs --tail=100 > debug_logs.txt

# Database info
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -c "\dt"
```

---

## Preventive Measures

### Regular Maintenance

```bash
# Weekly: Clean up old Docker resources
docker system prune -a --volumes

# Monthly: Vacuum database
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -c "VACUUM ANALYZE"

# Check disk space
df -h
```

### Monitor Resources

```bash
# Docker resource usage
docker stats

# Database size
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -c "
  SELECT pg_size_pretty(pg_database_size('llm_eaas'))
"
```

---

## Checklist for Fresh Install

- [ ] Docker and Docker Compose installed
- [ ] PostgreSQL container running (`docker compose ps`)
- [ ] Database initialized (`psql -f backend/db/schema.sql`)
- [ ] Backend .env configured
- [ ] Frontend .env.local configured
- [ ] LLM service running (Ollama or OpenAI key set)
- [ ] Backend starts without errors (`docker compose logs backend`)
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Health endpoint responds (`curl http://localhost:8000/health`)
- [ ] Can upload sample CSV
- [ ] Can run evaluation
- [ ] Can view results

---

## Still Stuck?

1. Review [Configuration Reference](CONFIGURATION_REFERENCE.md)
2. Check [API Documentation](API_DOCUMENTATION.md)
3. Consult [Deployment Guide](DEPLOYMENT_GUIDE.md)
4. Search logs for specific error messages
5. Test each component individually
6. Try a fresh install in a clean directory
