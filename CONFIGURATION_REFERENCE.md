# Configuration Reference

## Environment Variables

All configuration is managed through environment variables loaded from `.env` files. The application uses `pydantic-settings` for configuration management.

---

## Backend Configuration (`backend/.env`)

### Database Configuration

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `LLM_EAAS_DATABASE_URL` | String | N/A | ✅ Yes | Async SQLAlchemy database URL |

**Examples**:
```dotenv
# Local development with asyncpg
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/llm_eaas

# AWS RDS
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:password@llm-eaas-db.xxxxx.us-east-1.rds.amazonaws.com:5432/llm_eaas

# Azure Database for PostgreSQL
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres@servername:password@servername.postgres.database.azure.com:5432/llm_eaas
```

---

### LLM Provider Configuration

#### Ollama (Local, Recommended for Development)

```dotenv
LLM_EAAS_LLM_PROVIDER=ollama
LLM_EAAS_LLM_MODEL=llama3.2
LLM_EAAS_LLM_BASE_URL=http://localhost:11434/v1
LLM_EAAS_LLM_API_KEY=not-needed
```

**Available Ollama Models**:
- `llama3.2` (Recommended, 11B parameters)
- `llama2` (7B parameters)
- `mistral` (7B parameters)
- `neural-chat` (7B parameters)

**Setup Ollama**:
```bash
# Install Ollama: https://ollama.ai
# Pull model
ollama pull llama3.2

# Verify (should respond with model info)
curl http://localhost:11434/api/tags
```

#### OpenAI (Cloud, Production-Ready)

```dotenv
LLM_EAAS_LLM_PROVIDER=openai
LLM_EAAS_LLM_MODEL=gpt-4-mini
LLM_EAAS_LLM_BASE_URL=https://api.openai.com/v1
LLM_EAAS_OPENAI_API_KEY=sk-your-actual-key-here
```

**Available OpenAI Models**:
- `gpt-4-mini` (Recommended, fast & cheap)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

**Get API Key**:
1. Visit https://platform.openai.com/account/api-keys
2. Create new secret key
3. Copy and paste into `.env`

---

### LLM Behavior Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_EAAS_LLM_TIMEOUT_SECONDS` | Integer | 60 | Timeout for LLM API calls |
| `LLM_EAAS_JUDGE_TEMPERATURE_DEFAULT` | Float | 0.2 | Default temperature for judge model (0.0-1.0) |
| `LLM_EAAS_MAX_JUDGE_RETRIES` | Integer | 2 | Number of retries if LLM returns invalid JSON |

**Temperature Guide**:
- `0.0`: Deterministic, same input always gives same output
- `0.2-0.4`: Low temperature, consistent and focused (RECOMMENDED for evaluation)
- `0.5-0.7`: Medium temperature, balanced randomness
- `0.8-1.0`: High temperature, creative and diverse

---

### Application Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_EAAS_APP_NAME` | String | "LLM Evaluation-as-a-Service" | Application name |
| `LLM_EAAS_ENVIRONMENT` | String | "local" | Environment (local, staging, production) |
| `LLM_EAAS_ALLOWED_ORIGINS` | JSON List | `["http://localhost:3000"]` | CORS allowed origins |

**CORS Configuration Examples**:
```dotenv
# Development
LLM_EAAS_ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Production
LLM_EAAS_ALLOWED_ORIGINS=["https://app.example.com", "https://www.example.com"]

# Allow all (not recommended for production)
LLM_EAAS_ALLOWED_ORIGINS=["*"]
```

---

### Evaluation Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_EAAS_REGRESSION_THRESHOLD` | Float | 0.05 | Drop ratio threshold for detecting regression (0.0-1.0, as percentage: 0.05 = 5%) |
| `LLM_EAAS_BASELINE_EXPERIMENT_ID` | String (UUID) | None | Optional: Pin a specific experiment as baseline (auto-selects first baseline if not set) |

**Regression Threshold**:
- `0.01`: Very strict (1% drop triggers regression)
- `0.05`: Standard (5% drop triggers regression) **[RECOMMENDED]**
- `0.10`: Lenient (10% drop triggers regression)

**Example**:
```dotenv
# If baseline scores = 4.5, threshold = 0.05
# Candidate needs score >= 4.275 to pass (5% drop = 0.225)
# If candidate = 4.2, regression detected = true
LLM_EAAS_REGRESSION_THRESHOLD=0.05
```

---

## Frontend Configuration (`frontend/.env.local`)

### API Configuration

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | String | http://localhost:8000 | ✅ Yes | Base URL for backend API |

**Examples**:
```dotenv
# Local development
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Staging
NEXT_PUBLIC_API_BASE_URL=https://api-staging.example.com

# Production
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
```

---

## Docker Compose Configuration

### Environment Variables in docker-compose.yml

```yaml
services:
  backend:
    environment:
      LLM_EAAS_DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/llm_eaas
      LLM_EAAS_LLM_PROVIDER: ollama
      LLM_EAAS_LLM_MODEL: llama3.2
      LLM_EAAS_LLM_BASE_URL: http://ollama:11434/v1
      LLM_EAAS_ALLOWED_ORIGINS: '["http://localhost:3000"]'
      LLM_EAAS_REGRESSION_THRESHOLD: 0.05
      LLM_EAAS_MAX_JUDGE_RETRIES: 2

  postgres:
    environment:
      POSTGRES_DB: llm_eaas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

  ollama:
    # No additional env vars needed
```

---

## Configuration by Deployment Type

### Local Development

**backend/.env**:
```dotenv
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/llm_eaas
LLM_EAAS_LLM_PROVIDER=ollama
LLM_EAAS_LLM_MODEL=llama3.2
LLM_EAAS_LLM_BASE_URL=http://localhost:11434/v1
LLM_EAAS_ALLOWED_ORIGINS=["http://localhost:3000"]
LLM_EAAS_ENVIRONMENT=local
```

**frontend/.env.local**:
```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Docker Compose

**docker-compose.yml** (referential, service-to-service communication):
```yaml
...
backend:
  environment:
    LLM_EAAS_DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/llm_eaas
    LLM_EAAS_LLM_BASE_URL: http://ollama:11434/v1
  depends_on:
    - postgres
    - ollama
```

### Staging (AWS ECS)

**Task Definition Environment**:
```json
"environment": [
  {
    "name": "LLM_EAAS_DATABASE_URL",
    "value": "postgresql+asyncpg://postgres:SECURED@llm-eaas-db-staging.xxxxx.rds.amazonaws.com:5432/llm_eaas"
  },
  {
    "name": "LLM_EAAS_LLM_PROVIDER",
    "value": "openai"
  },
  {
    "name": "LLM_EAAS_OPENAI_API_KEY",
    "valueFrom": "arn:aws:secretsmanager:..."
  },
  {
    "name": "LLM_EAAS_ENVIRONMENT",
    "value": "staging"
  },
  {
    "name": "LLM_EAAS_ALLOWED_ORIGINS",
    "value": "[\"https://staging.example.com\"]"
  }
]
```

### Production (AWS RDS + ECS)

**Secrets Manager** (recommended approach):
```bash
# Store sensitive values
aws secretsmanager create-secret \
  --name llm-eaas/database-url \
  --secret-string "postgresql+asyncpg://postgres:SECURE_PASSWORD@llm-eaas-db-prod.xxxxx.rds.amazonaws.com:5432/llm_eaas"

aws secretsmanager create-secret \
  --name llm-eaas/openai-api-key \
  --secret-string "sk-..."
```

**Task Definition**:
```json
"environment": [
  {
    "name": "LLM_EAAS_LLM_PROVIDER",
    "value": "openai"
  },
  {
    "name": "LLM_EAAS_LLM_MODEL",
    "value": "gpt-4-mini"
  },
  {
    "name": "LLM_EAAS_ENVIRONMENT",
    "value": "production"
  },
  {
    "name": "LLM_EAAS_ALLOWED_ORIGINS",
    "value": "[\"https://app.example.com\", \"https://www.example.com\"]"
  },
  {
    "name": "LLM_EAAS_REGRESSION_THRESHOLD",
    "value": "0.05"
  }
],
"secrets": [
  {
    "name": "LLM_EAAS_DATABASE_URL",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:llm-eaas/database-url:database_url::"
  },
  {
    "name": "LLM_EAAS_OPENAI_API_KEY",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:llm-eaas/openai-api-key:api_key::"
  }
]
```

---

## Database Configuration

### Connection String Format

```
postgresql+asyncpg://username:password@host:port/database
```

### Connection Pool Settings

Default SQLAlchemy async settings:
- **pool_pre_ping**: `True` (verify connections before use)
- **pool_recycle**: `3600` (recycle connections after 1 hour)

### Performance Tuning

For high-traffic deployments, consider:

```python
# In app/db/session.py
async_engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,           # Number of DB connections to keep
    max_overflow=10,        # Additional connections if needed
    pool_recycle=3600,      # Recycle after 1 hour
    echo=False,             # Set to True for SQL debugging
)
```

---

## Logging Configuration

### Log Levels

Default: `INFO`

Levels (in increasing verbosity):
- `CRITICAL`: System is unusable
- `ERROR`: Something failed
- `WARNING`: Something unexpected happened
- `INFO`: General informational messages
- `DEBUG`: Detailed information (development only)

### View Logs

**Docker**:
```bash
docker compose logs -f backend      # Last 100 lines, follow
docker compose logs backend -n 50    # Last 50 lines
```

**Local Development**:
```
Logs appear in terminal where uvicorn is running
```

---

## Health Check Configuration

### Recommended Health Check Settings

**Docker Compose**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**AWS ECS**:
```json
"healthCheck": {
  "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
  "interval": 30,
  "timeout": 5,
  "retries": 3,
  "startPeriod": 60
}
```

---

## Feature Flags

While not implemented yet, you can add feature flag support:

```python
# Add to Settings class in core/config.py
enable_regression_check: bool = Field(default=True)
enable_safety_scoring: bool = Field(default=True)
```

---

## Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use secure password generator** for database passwords
3. **Rotate API keys regularly** (every 90 days)
4. **Use HTTPS in production** - Always
5. **Restrict database access** - Use security groups/firewalls
6. **Monitor for unusual activity** - Check logs regularly
7. **Use managed secrets service** - AWS Secrets Manager, Azure Key Vault, etc.
8. **Implement rate limiting** - At reverse proxy level
9. **Use environment-specific secrets** - Never use production credentials in development

---

## Validation

### Configuration Validation Examples

```bash
# Test backend configuration
cd backend
python3 -c "from app.core.config import get_settings; settings = get_settings(); print(f'Database: {settings.database_url}'); print(f'Provider: {settings.llm_provider}')"

# Should output without errors
```

---

## Configuration Checklist

- [ ] Set correct `LLM_EAAS_DATABASE_URL`
- [ ] Choose LLM provider (ollama or openai)
- [ ] Configure LLM API key if using OpenAI
- [ ] Set `ALLOWED_ORIGINS` for CORS
- [ ] Configure regression threshold for your use case
- [ ] Set appropriate timeout values
- [ ] Update frontend `NEXT_PUBLIC_API_BASE_URL`
- [ ] Remove `.env` files before committing
- [ ] Test configuration before deployment

---

## Common Configuration Issues

**"Invalid database URL"**
```
Check format: postgresql+asyncpg://user:pass@host:port/db
```

**"Could not connect to LLM"**
```
Verify LLM_EAAS_LLM_BASE_URL is correct and service is running
For Ollama: http://localhost:11434/v1
For OpenAI: https://api.openai.com/v1
```

**"CORS error in browser"**
```
Check frontend NEXT_PUBLIC_API_BASE_URL
Ensure backend ALLOWED_ORIGINS includes frontend URL
```

**"Temperature out of range"**
```
Must be between 0.0 and 1.0
```
