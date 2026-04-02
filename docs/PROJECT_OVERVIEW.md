# LLM EaaS - Project Overview

## What It Is
LLM EaaS (LLM Evaluation-as-a-Service) is a platform to evaluate LLM outputs in a structured and repeatable way.

Instead of manual spot-checking, the system automates quality scoring with rubrics, aggregates metrics, and compares experiments to detect regressions.

## Why It Exists
Model quality can silently degrade when prompts, models, or evaluation logic change.

This platform exists to provide:
- consistent evaluation standards
- measurable quality outcomes
- automated regression detection
- release gating signals for safer deployments

## Core Workflow
1. Upload a dataset (CSV).
2. Define evaluation rubric criteria.
3. Run LLM-as-judge evaluation.
4. Store item-level and aggregate metrics.
5. Compare candidate experiment vs baseline.
6. Use CI gate output for go/no-go decisions.

## Core Capabilities
- Dataset ingestion and validation
- Rubric-driven scoring
- Experiment lifecycle tracking
- Baseline/candidate comparison
- CI gate endpoint support
- Advanced metrics and summaries
- Structured logging and observability
- API key auth and rate limiting
- Export/report support

## Why This Stack
### Backend: FastAPI + SQLAlchemy
- Strong fit for Python-first LLM workflows.
- Async support, typing, and automatic API docs.
- Mature ORM and migration ecosystem.

Why not Flask/Django/Express:
- Flask is lighter but adds manual structure overhead.
- Django is powerful but heavier than needed for API-first evaluation.
- Express is viable, but Python ecosystem is better aligned for LLM/data processing.

### Frontend: Next.js + TypeScript
- Rapid UI development with stable production tooling.
- Better API integration safety with TypeScript.

Why not plain React/Angular/Vue:
- Plain React requires more assembly for app structure.
- Angular adds framework overhead for this scope.
- Vue is valid, but team alignment favored React ecosystem.

### Database: PostgreSQL
- Reliable relational model for experiments and metrics.
- Strong query support and mature operations tooling.

Why not SQLite/MongoDB:
- SQLite is ideal for local dev, limited for concurrent production usage.
- MongoDB is flexible, but this domain benefits from relational constraints and joins.

### LLM Provider Abstraction
- Prevents vendor lock-in.
- Supports free/local/provider-specific optimization by environment.

## Business Outcome
- Reduces manual review effort
- Improves confidence in model releases
- Enables measurable quality standards
- Makes evaluation auditable and repeatable

## One-Line Summary
A production-style platform to evaluate, compare, and gate LLM output quality before deployment.
