# Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment-aws-gcp-azure)
4. [Production Checklist](#production-checklist)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Scaling](#scaling)

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose
- Git

### Quick Start

#### 1. Clone & Setup
```bash
cd /Users/utkarshraj/LLM\ EaaS
git clone <repo-url> .  # if not already done

# Install backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

#### 2. Start PostgreSQL
```bash
docker compose up -d
# Verify: docker ps (should show pgvector container)
```

#### 3. Initialize Database
```bash
psql postgresql://postgres:postgres@localhost:5432/llm_eaas -f backend/db/schema.sql
```

#### 4. Configure Environment

**Backend** (`backend/.env`):
```dotenv
LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/llm_eaas
LLM_EAAS_LLM_PROVIDER=ollama  # or "openai"
LLM_EAAS_LLM_MODEL=llama3.2
LLM_EAAS_LLM_BASE_URL=http://localhost:11434/v1
LLM_EAAS_LLM_API_KEY=not-needed
LLM_EAAS_ALLOWED_ORIGINS=["http://localhost:3000"]
LLM_EAAS_REGRESSION_THRESHOLD=0.05
LLM_EAAS_MAX_JUDGE_RETRIES=2
```

**Frontend** (`frontend/.env.local`):
```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### 5. Start Services

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
# Access: http://localhost:3000
```

#### 6. Verify Setup
- API Health: `curl http://localhost:8000/health`
- Frontend: Navigate to `http://localhost:3000`
- Test with sample data: `sample_data.csv`

---

## Docker Deployment

### Build Docker Images

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine

WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]
```

#### Updated docker-compose.yml
```yaml
version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: llm_eaas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      LLM_EAAS_DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/llm_eaas
      LLM_EAAS_LLM_PROVIDER: ollama
      LLM_EAAS_LLM_BASE_URL: http://ollama:11434/v1
      LLM_EAAS_ALLOWED_ORIGINS: '["http://localhost:3000", "http://frontend:3000"]'
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app  # For development; remove for production

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  pgdata:
  ollama_data:
```

### Build & Run

```bash
# Build images
docker compose build

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Remove volumes (careful!)
docker compose down -v
```

---

## Cloud Deployment (AWS/GCP/Azure)

### AWS Deployment

#### 1. RDS PostgreSQL Setup
```bash
# Via AWS Console or AWS CLI
aws rds create-db-instance \
  --db-instance-identifier llm-eaas-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password <secure-password> \
  --allocated-storage 20 \
  --publicly-accessible false
```

#### 2. ECS Container Registry
```bash
# Push images to ECR
aws ecr create-repository --repository-name llm-eaas-backend
aws ecr create-repository --repository-name llm-eaas-frontend

# Build and push
docker build -t llm-eaas-backend backend/
docker tag llm-eaas-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/llm-eaas-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/llm-eaas-backend:latest
```

#### 3. ECS Task Definition (backend)
```json
{
  "family": "llm-eaas-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/llm-eaas-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LLM_EAAS_DATABASE_URL",
          "value": "postgresql+asyncpg://postgres:<password>@llm-eaas-db.xxxxx.us-east-1.rds.amazonaws.com:5432/llm_eaas"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/llm-eaas",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### GCP Deployment

#### 1. Cloud SQL PostgreSQL
```bash
gcloud sql instances create llm-eaas-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1
```

#### 2. Artifact Registry
```bash
# Push image
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/llm-eaas/backend:latest backend/
```

#### 3. Cloud Run Deployment
```bash
gcloud run deploy llm-eaas-backend \
  --image us-central1-docker.pkg.dev/PROJECT_ID/llm-eaas/backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --set-env-vars LLM_EAAS_DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@CLOUD_SQL_IP:5432/llm_eaas \
  --allow-unauthenticated
```

### Azure Deployment

#### 1. Azure Database for PostgreSQL
```bash
az postgres server create \
  --resource-group llm-eaas-rg \
  --name llm-eaas-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password <secure-password> \
  --sku-name B_Gen5_1
```

#### 2. Container Registry
```bash
az acr create --resource-group llm-eaas-rg --name llmeasreg --sku Basic

# Push image
az acr build --registry llmeasreg --image llm-eaas-backend:latest backend/
```

#### 3. App Service Deployment
```bash
az webapp create \
  --resource-group llm-eaas-rg \
  --plan llm-eaas-plan \
  --name llm-eaas-backend \
  --deployment-container-image-name llmeasreg.azurecr.io/llm-eaas-backend:latest

az webapp config appsettings set \
  --resource-group llm-eaas-rg \
  --name llm-eaas-backend \
  --settings LLM_EAAS_DATABASE_URL=postgresql+asyncpg://...
```

---

## Production Checklist

### Security
- [ ] Enable HTTPS/TLS on all endpoints
- [ ] Set strong database password
- [ ] Configure firewall rules (restrict database access)
- [ ] Use environment variables for secrets (never commit .env)
- [ ] Enable database encryption at rest
- [ ] Set up API key authentication if needed
- [ ] Configure CORS properly (whitelist specific origins)
- [ ] Use managed secrets service (AWS Secrets Manager, Azure Key Vault, etc.)

### Performance
- [ ] Configure database connection pooling
- [ ] Enable caching headers on frontend
- [ ] Set up CDN for static assets
- [ ] Configure appropriate timeout values
- [ ] Set up load balancing for backend services

### Monitoring & Logging
- [ ] Set up centralized logging (CloudWatch, Stackdriver, etc.)
- [ ] Configure alerts for errors and exceptions
- [ ] Enable database monitoring and backups
- [ ] Set up uptime monitoring
- [ ] Configure performance metrics collection

### Data
- [ ] Enable automated daily backups
- [ ] Test backup restore procedure
- [ ] Set up database replica for failover
- [ ] Configure retention policies

### Deployment
- [ ] Set up CI/CD pipeline
- [ ] Configure health checks
- [ ] Enable auto-scaling based on load
- [ ] Set up staged deployment (dev → staging → production)
- [ ] Document rollback procedure

### Documentation
- [ ] Document all environment variables
- [ ] Create runbook for common issues
- [ ] Document deployment procedure
- [ ] List all external dependencies

---

## Monitoring & Maintenance

### Health Checks

**Endpoint**: `GET /health`
```bash
# Setup in load balancer or monitoring service
- Check every 30 seconds
- Timeout: 10 seconds
- Healthy threshold: 2 consecutive checks
- Unhealthy threshold: 3 consecutive failures
```

### Logs

**Backend Logs**:
```bash
# Docker
docker compose logs -f backend

# Kubernetes
kubectl logs -f deployment/llm-eaas-backend

# Cloud Run (GCP)
gcloud run logs read llm-eaas-backend
```

### Database Maintenance

**Backup**:
```bash
# Local backup
pg_dump postgresql://postgres:password@localhost:5432/llm_eaas > backup.sql

# Restore
psql postgresql://postgres:password@localhost:5432/llm_eaas < backup.sql
```

**Cleanup Old Experiments** (optional):
```sql
DELETE FROM experiments 
WHERE created_at < NOW() - INTERVAL '90 days' 
  AND status = 'completed';
```

### Updating LLM Model

```bash
# Update .env or docker-compose environment
LLM_EAAS_LLM_MODEL=llama2  # Change from llama3.2

# Restart backend
docker compose restart backend
```

---

## Scaling

### Horizontal Scaling (Multiple Backend Instances)

**Docker Compose (Local)**:
```bash
docker compose up -d --scale backend=3
```

**Kubernetes**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-eaas-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-eaas-backend
  template:
    metadata:
      labels:
        app: llm-eaas-backend
    spec:
      containers:
      - name: backend
        image: llm-eaas-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_EAAS_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: llm-eaas-secrets
              key: database-url
```

### Database Scaling

**Read Replicas** (for query-heavy workloads):
```bash
# AWS RDS
aws rds create-db-instance-read-replica \
  --db-instance-identifier llm-eaas-db-replica \
  --source-db-instance-identifier llm-eaas-db
```

### Connection Pooling

**PgBouncer Configuration**:
```ini
[databases]
llm_eaas = host=localhost port=5432 dbname=llm_eaas

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
```

---

## Troubleshooting Deployment Issues

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection string
psql postgresql://postgres:postgres@localhost:5432/llm_eaas

# Verify network (Docker)
docker network ls
```

### Backend fails to start
```bash
# Check logs
docker compose logs backend

# Verify environment variables
docker compose config

# Rebuild image
docker compose build --no-cache backend
```

### Frontend API calls fail
```bash
# Check CORS settings
# Ensure NEXT_PUBLIC_API_BASE_URL matches backend URL
# Check backend is accessible from frontend container

# Test API manually
curl http://backend:8000/health
```

### Slow evaluation performance
- Increase timeout values
- Check LLM service availability
- Reduce batch size
- Scale up backend instances

---

## Disaster Recovery

### Backup Strategy
- Daily automated backups
- Weekly encrypted backups to cold storage
- Monthly backup restore test

### Recovery Procedure
1. Restore database from latest backup
2. Verify data integrity
3. Restart backend services
4. Run health checks
5. Notify users

### RTO/RPO Targets
- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 24 hours

---

## Next Steps

1. Test locally with sample data (`sample_data.csv`)
2. Deploy to staging environment
3. Run load testing
4. Deploy to production
5. Set up monitoring and alerts
