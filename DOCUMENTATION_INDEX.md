# 📑 Documentation Index

**Last Updated**: March 24, 2026  
**Project**: LLM Evaluation-as-a-Service (EaaS)  
**Status**: ✅ Production Ready

---

## 🎯 Start Here

### New to the Project?
1. **[README.md](README.md)** - 5-minute overview & quickstart
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common commands & endpoints
3. **[sample_data.csv](sample_data.csv)** - Test data for first evaluation

### Ready to Deploy?
1. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Platform-specific deployment
2. **[OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)** - Day-of-deployment runbook & smoke tests
3. **[CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)** - Environment setup
4. **[PROJECT_DELIVERY_REPORT.md](PROJECT_DELIVERY_REPORT.md)** - What's included & next steps

### Need Help?
1. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues & solutions
2. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - API reference for integration
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick lookup card

---

## 📚 Complete Documentation

### Overview & Getting Started

#### [README.md](README.md) - Main Project README
- **Length**: 350 lines
- **Purpose**: Project overview, quick start, feature summary
- **Audience**: Everyone
- **Key Sections**:
  - 5-minute quickstart
  - Core features list
  - Architecture diagram
  - API endpoints overview
  - Deployment options
  - Testing guide
  - Support resources

#### [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick Lookup Card
- **Length**: 300 lines
- **Purpose**: Quick commands, checklists, troubleshooting lookup
- **Audience**: Developers, DevOps
- **Key Content**:
  - Start services commands
  - Project structure
  - Key endpoints table
  - Sample rubric
  - Quick troubleshooting
  - Docker commands
  - Deployment quick links

---

### API Reference

#### [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API Reference
- **Length**: 550 lines
- **Purpose**: Detailed API documentation with examples
- **Audience**: API users, integration developers
- **Key Sections**:
  - Overview & base URL
  - All 6 endpoints with detailed documentation:
    - GET /health
    - POST /experiments/upload
    - POST /experiments/run
    - GET /experiments/{id}
    - GET /experiments/compare
    - GET /experiments/{id}/ci-gate
  - Request/response examples
  - Error handling
  - Complete workflow examples
  - Rubric definition guide
  - Metrics explanation
  - Performance considerations
  - Rate limiting

**API Endpoints Documented**:
```
GET /health                          → Health check
POST /experiments/upload             → Create experiment from CSV
POST /experiments/run                → Run evaluation with rubric
GET /experiments/{id}                → Get results & metrics
GET /experiments/compare             → Compare two experiments
GET /experiments/{id}/ci-gate        → Check deployment gate
```

---

### Deployment & Infrastructure

#### [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete Deployment Guide
- **Length**: 800 lines
- **Purpose**: Deploy to any platform (local, Docker, cloud)
- **Audience**: DevOps, system administrators
- **Key Sections**:
  - Local development setup (step-by-step)
  - Docker & Docker Compose
  - Cloud deployments:
    - AWS (RDS, ECR, ECS)
    - GCP (Cloud SQL, Artifact Registry, Cloud Run)
    - Azure (Azure Database, App Service)
  - Production checklist
  - Monitoring & maintenance
  - Scaling strategies
  - Disaster recovery
  - Backup procedures

**Deployment Platforms Covered**:
```
✅ Local development     (5 min setup)
✅ Docker Compose        (1 command)
✅ AWS (ECS + RDS)       (30 min setup)
✅ GCP (Cloud Run)       (30 min setup)
✅ Azure (App Service)   (30 min setup)
✅ Kubernetes            (manifests provided)
```

---

### Configuration & Settings

#### [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Configuration Reference
- **Length**: 450 lines
- **Purpose**: Document all environment variables & settings
- **Audience**: System administrators, DevOps
- **Key Sections**:
  - Backend environment variables (organized by category)
  - Frontend environment variables
  - LLM provider setup (Ollama vs OpenAI)
  - Database configuration
  - Health check configuration
  - Config examples by deployment type:
    - Local development
    - Docker Compose
    - Staging (AWS)
    - Production (AWS)
  - Security best practices
  - Common configuration issues

**Environment Variables Documented**:
```
Database:      LLM_EAAS_DATABASE_URL
LLM Provider:  LLM_EAAS_LLM_PROVIDER, MODEL, BASE_URL, API_KEY
Evaluation:    JUDGE_TEMPERATURE_DEFAULT, MAX_JUDGE_RETRIES
Baseline:      LLM_EAAS_BASELINE_EXPERIMENT_ID
CORS:          LLM_EAAS_ALLOWED_ORIGINS
Regression:    LLM_EAAS_REGRESSION_THRESHOLD
... and more
```

---

### Support & Troubleshooting

#### [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting Guide
- **Length**: 600 lines
- **Purpose**: Resolve common issues and problems
- **Audience**: Everyone (developers, users, operators)
- **Key Sections**:
  - Quick diagnosis commands
  - 8 major issue categories:
    1. Database connection issues
    2. LLM provider issues
    3. Frontend API issues
    4. Performance problems
    5. Docker issues
    6. API errors
    7. Data issues
    8. Testing issues
  - Debugging techniques
  - Emergency recovery procedures
  - Logging best practices
  - Fresh install checklist
  - Preventive maintenance

**Issue Categories Covered**:
```
Database:       Connection, SSL, schema
LLM:            Ollama, OpenAI, JSON response
Frontend:       API calls, CSV validation
Performance:    Slow evaluation, slow queries
Docker:         Port conflicts, restart loops
API:            Not found, no baseline configured
Data:           Missing items, safety fail rate
Testing:        Database errors
```

---

### Project Information

#### [DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md) - Documentation Summary
- **Length**: 250 lines
- **Purpose**: Summary of all documentation & deliverables
- **Audience**: Project managers, stakeholders
- **Key Content**:
  - Files created & purpose
  - Documentation statistics
  - Coverage matrix
  - What's included checklist
  - Next steps for deployment

#### [PROJECT_DELIVERY_REPORT.md](PROJECT_DELIVERY_REPORT.md) - Delivery Report
- **Length**: 400 lines
- **Purpose**: Complete project status & delivery summary
- **Audience**: Project stakeholders, teams
- **Key Sections**:
  - Executive summary
  - Completion matrix
  - What's included
  - Getting started (5 min)
  - API endpoints overview
  - Quality metrics
  - Deployment options with pricing
  - Configuration examples
  - Next steps

---

## 📊 Test Data

### [sample_data.csv](sample_data.csv) - Sample Evaluation Data
- **Size**: 10 evaluation samples
- **Format**: CSV (prompt, model_output, reference_output)
- **Domains**: Science, technology, knowledge
- **Purpose**: Testing evaluation workflow
- **Usage**:
  ```bash
  # Upload via frontend or API
  curl -X POST -F "file=@sample_data.csv" http://localhost:8000/experiments/upload
  ```

---

## 🐳 Infrastructure Files

### Docker Files

#### [backend/Dockerfile](backend/Dockerfile)
- Production-ready backend image
- Python 3.11-slim base
- Health check configured
- Security best practices

#### [frontend/Dockerfile](frontend/Dockerfile)
- Multi-stage build for optimization
- Node.js 18-alpine
- Health check configured
- Production dependencies only

### Project Configuration

#### [.gitignore](.gitignore)
- Comprehensive ignore patterns
- Python, Node.js, IDE, OS
- Environment files excluded
- Database backups ignored

---

## 📋 Documentation Navigation Guide

```
START HERE
    ↓
README.md (overview)
    ↓
    ├─→ QUICK_REFERENCE.md (for quick lookup)
    │
    ├─→ For API Integration:
    │   └─→ API_DOCUMENTATION.md
    │
    ├─→ For Deployment:
    │   └─→ DEPLOYMENT_GUIDE.md
    │       ├─→ CONFIGURATION_REFERENCE.md
    │       └─→ TROUBLESHOOTING.md
    │
    └─→ For Project Info:
        └─→ PROJECT_DELIVERY_REPORT.md
        └─→ DOCUMENTATION_SUMMARY.md
```

---

## 🎯 By Role

### Software Developer
1. [README.md](README.md) - Overview
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick commands
3. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
4. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Debugging

### DevOps/System Administrator
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment
2. [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Settings
3. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Operations

### API User/Integrator
1. [README.md](README.md) - Overview
2. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick lookup
4. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Issues

### Project Manager/Stakeholder
1. [README.md](README.md) - Overview
2. [PROJECT_DELIVERY_REPORT.md](PROJECT_DELIVERY_REPORT.md) - Status
3. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment plan
4. [DOCUMENTATION_SUMMARY.md](DOCUMENTATION_SUMMARY.md) - Deliverables

---

## 📊 Documentation Statistics

| Document | Lines | Focus | For |
|----------|-------|-------|-----|
| README.md | 350 | Overview & quick start | Everyone |
| API_DOCUMENTATION.md | 550 | API reference | Developers |
| DEPLOYMENT_GUIDE.md | 800 | Cloud & local deployment | DevOps |
| CONFIGURATION_REFERENCE.md | 450 | Environment setup | System Admins |
| TROUBLESHOOTING.md | 600 | Issue resolution | Support |
| QUICK_REFERENCE.md | 300 | Quick commands | Everyone |
| PROJECT_DELIVERY_REPORT.md | 400 | Project status | Stakeholders |
| DOCUMENTATION_SUMMARY.md | 250 | Deliverables | Managers |
| **TOTAL** | **3,700** | **Complete System** | **All Users** |

---

## ✅ What's Documented

### Implementation
- ✅ Backend (FastAPI, 6 endpoints)
- ✅ Frontend (Next.js, full UI)
- ✅ Database (PostgreSQL, 4 tables)
- ✅ LLM Integration (Ollama + OpenAI)
- ✅ Docker setup (production images)

### Operations
- ✅ Local development setup
- ✅ Docker Compose deployment
- ✅ Cloud deployment (5 platforms)
- ✅ Configuration (all env vars)
- ✅ Troubleshooting (8 categories)
- ✅ Monitoring & logging
- ✅ Backup & disaster recovery
- ✅ Scaling strategies

### Usage
- ✅ API reference
- ✅ Example workflows
- ✅ Rubric definition
- ✅ Sample data
- ✅ Quick reference
- ✅ Common commands

---

## 🔄 Recommended Reading Order

### First Time Setup
1. [README.md](README.md) - 10 min
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 5 min
3. Start services - 2 min
4. Test with [sample_data.csv](sample_data.csv) - 5 min
5. **Total: 22 minutes to first evaluation**

### Before Deployment
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 30 min
2. [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - 15 min
3. Review deployment checklist - 10 min
4. **Total: 55 minutes before production deployment**

### For Integration
1. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - 30 min
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 5 min
3. Test with sample data - 10 min
4. **Total: 45 minutes for API integration**

### For Troubleshooting
1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Find issue category
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick diagnosis
3. Check [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) if config issue
4. **Total: 5-15 minutes depending on issue**

---

## 🚀 Next Steps

1. **Read** [README.md](README.md) - Understand the project
2. **Setup** - Follow quick start in README
3. **Test** - Upload sample_data.csv, run evaluation
4. **Explore** - Try API endpoints documented in [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
5. **Deploy** - Choose platform and follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
6. **Configure** - Use [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for production setup
7. **Monitor** - Follow logging practices from [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 💡 Quick Links

**Confused? Use these links**:
- "How do I start?" → [README.md](README.md)
- "What commands do I need?" → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- "How do I use the API?" → [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- "How do I deploy?" → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- "What do I configure?" → [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)
- "Something's broken" → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- "What's included?" → [PROJECT_DELIVERY_REPORT.md](PROJECT_DELIVERY_REPORT.md)

---

**Status**: ✅ All documentation complete  
**Ready**: Yes, for production deployment  
**Last Updated**: February 19, 2026
