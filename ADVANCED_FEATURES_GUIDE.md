# Advanced Features Guide

## Overview

This document describes the new production-ready features added to the LLM EaaS platform to optimize performance, security, and scalability.

---

## 1. API Authentication & Key Management

### Overview
Secure API access using API keys with rate limiting and role-based controls.

### Features
- **API Key Generation**: Create unique, cryptographically secure API keys
- **Rate Limiting**: Control requests per hour per API key
- **Expiration**: Set expiration dates on keys
- **Audit Trail**: Track last usage and activity
- **Scopes**: Manage what operations each key can perform

### Usage

#### Creating an API Key
```python
from app.core.auth import generate_api_key, hash_api_key

# Generate new key
api_key = generate_api_key()  # Returns: sk_xxxxxxxxxxxxx
key_hash = hash_api_key(api_key)  # Store this hash in DB
```

#### Using API Keys in Requests
```bash
curl -X POST http://localhost:8000/api/experiments/run \
  -H "X-API-Key: sk_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"experiment_id": "uuid"}'
```

#### FastAPI Endpoint Protection
```python
from fastapi import Depends
from app.core.auth import check_rate_limit

@app.post("/experiments/run")
async def run_experiment(
    api_key = Depends(check_rate_limit),  # Validates and rate-limits
    # ... rest of function
):
    pass
```

### Configuration
Set in `.env`:
```
API_KEY_EXPIRATION_DAYS=365
DEFAULT_RATE_LIMIT=1000  # requests per hour
```

---

## 2. Advanced Metrics & Statistical Analysis

### Overview
Comprehensive statistical analysis beyond mean/std dev for production-grade evaluations.

### Features
- **Percentiles**: P25, P50, P75, P95, P99
- **Confidence Intervals**: 95% and 99% CI
- **Distribution Analysis**: Skewness and kurtosis
- **Effect Size**: Cohen's d for comparisons
- **Statistical Tests**: T-test, Mann-Whitney U, Welch's t-test

### Usage

#### Calculate Advanced Metrics
```python
from app.services.advanced_metrics import calculate_advanced_metrics

scores = [8.5, 9.0, 7.5, 8.8, 9.2, 8.1, 9.5, 8.3]
safety_failures = 1
total_items = len(scores)

metrics = calculate_advanced_metrics(
    scores=scores,
    safety_failures=safety_failures,
    total_items=total_items
)

print(f"Mean: {metrics.mean_score}")
print(f"95% CI: {metrics.confidence_interval_95}")
print(f"P95: {metrics.percentile_95}")
```

#### Compare Two Experiments
```python
from app.services.advanced_metrics import compare_distributions

scores_exp1 = [8.5, 9.0, 7.5, 8.8, 9.2]
scores_exp2 = [7.2, 7.8, 8.1, 7.5, 8.3]

comparison = compare_distributions(scores_exp1, scores_exp2)

print(f"Cohen's d: {comparison['cohens_d']}")
print(f"Effect size: {comparison['effect_size_interpretation']}")
print(f"T-test p-value: {comparison['t_test']['p_value']}")
print(f"Statistically significant: {comparison['t_test']['significant']}")
```

### Metrics Returned
```
- mean_score, median_score, std_dev
- percentile_25, percentile_50, percentile_75, percentile_95, percentile_99
- confidence_interval_95, confidence_interval_99
- skewness, kurtosis
- coefficient_of_variation
- safety_fail_rate
```

---

## 3. Batch Processing & Parallel Evaluation

### Overview
Efficiently process large datasets with concurrent batch processing and retry logic.

### Features
- **Configurable Batch Size**: Process items in optimal chunks
- **Concurrent Processing**: Multiple batches in parallel
- **Retry Logic**: Automatic retries with exponential backoff
- **Timeout Handling**: Per-item timeout protection
- **Progress Tracking**: Real-time completion status

### Usage

#### Configure Batch Processing
```python
from app.services.batch_processing import BatchProcessor, BatchConfig

config = BatchConfig(
    batch_size=10,              # Items per batch
    concurrent_batches=3,       # Concurrent batches
    retry_on_failure=True,
    max_retries=3,
    timeout_per_item=30         # seconds
)

processor = BatchProcessor(config)
```

#### Process Experiment Items
```python
from app.services.batch_processing import BatchResult

async def process_items(experiment_id: UUID, session: AsyncSession):
    # Define processing function
    async def evaluate_item(item):
        # Your evaluation logic here
        return await llm_evaluation_client.evaluate(item)
    
    result = BatchResult(total_items=0, successful=0, failed=0, errors=[])
    result = await processor.process_items(
        experiment_id=experiment_id,
        session=session,
        process_fn=evaluate_item,
        batch_result=result
    )
    
    print(f"Processed {result.successful}/{result.total_items}")
    print(f"Failures: {result.failed}")
```

#### Parallel Evaluation
```python
from app.services.batch_processing import ParallelEvaluator

evaluator = ParallelEvaluator(max_workers=5, chunk_size=10)

results = await evaluator.evaluate_parallel(
    items=evaluation_items,
    evaluate_fn=async_evaluate_function
)
```

---

## 4. Multi-Format Export

### Overview
Export experiments and results in JSON, CSV, HTML, or PDF formats.

### Features
- **JSON Export**: Full data with metadata
- **CSV Export**: Tabular format with metadata option
- **HTML Export**: Interactive table view
- **PDF Export**: Professional formatted report

### Usage

#### Export to JSON
```python
from app.services.export_service import ExperimentExporter

exporter = ExperimentExporter()

json_data = exporter.to_json(
    experiment_data={
        "id": "exp-123",
        "name": "My Experiment",
        "status": "completed"
    },
    results=[
        {"item_id": "1", "score": 8.5, "reasoning": "..."},
        {"item_id": "2", "score": 9.0, "reasoning": "..."}
    ]
)
```

#### Export to CSV
```python
csv_data = exporter.to_csv(
    experiment_data=experiment_dict,
    results=results_list,
    include_metadata=True
)

with open("results.csv", "w") as f:
    f.write(csv_data)
```

#### Export to PDF
```python
pdf_bytes = exporter.to_pdf(
    experiment_data=experiment_dict,
    results=results_list
)

with open("results.pdf", "wb") as f:
    f.write(pdf_bytes)
```

#### Export to HTML
```python
html_data = exporter.to_html(
    experiment_data=experiment_dict,
    results=results_list
)

with open("results.html", "w") as f:
    f.write(html_data)
```

---

## 5. Redis Caching Layer

### Overview
High-performance caching for frequently accessed results and metrics.

### Features
- **Configurable TTL**: Custom expiration per cache entry
- **Pattern Matching**: Invalidate related cache entries
- **Automatic Serialization**: JSON encoding/decoding
- **Fallback Mode**: Works without Redis installed
- **Connection Pooling**: Efficient resource usage

### Setup

#### Installation
```bash
pip install redis[asyncio]

# Start Redis server
docker run -d -p 6379:6379 redis:latest
```

#### Configure in `.env`
```
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

### Usage

#### Initialize Cache
```python
from app.core.cache import RedisCache, CachedMetricsService

cache = RedisCache(redis_url="redis://localhost:6379/0")
await cache.connect()

metrics_service = CachedMetricsService(cache)
```

#### Cache Metrics
```python
# Set metrics in cache (24 hour TTL)
await metrics_service.set_metrics(
    experiment_id="exp-123",
    metrics={"mean": 8.5, "std_dev": 0.8},
    ttl=86400
)

# Retrieve from cache
metrics = await metrics_service.get_metrics("exp-123")
if metrics:
    print("Retrieved from cache:", metrics)
```

#### Pattern-Based Invalidation
```python
from app.core.cache import CacheKeyBuilder

# Invalidate all data for an experiment
pattern = CacheKeyBuilder.experiment_pattern("exp-123")
await cache.invalidate_pattern(pattern)
```

---

## 6. Structured Logging & Observability

### Overview
Production-grade structured logging with JSON output for easy parsing and monitoring.

### Features
- **JSON Format**: Structured logs for log aggregation
- **Context Tracking**: Automatic context injection
- **Performance Timing**: Function execution duration
- **Request Logging**: HTTP request tracking
- **Error Tracking**: Exception context preservation

### Setup

#### Installation
```bash
pip install python-json-logger
```

### Usage

#### Setup Logging
```python
from app.core.structured_logging import setup_structured_logging

logger = setup_structured_logging(
    name="llm_eaas",
    level=logging.INFO,
    use_json=True
)
```

#### Log with Context
```python
from app.core.structured_logging import StructuredLogger

logger = StructuredLogger(logging.getLogger("app"))

# Set context for request
logger.set_context(request_id="req-123", user_id="user-456")

# All logs include context
logger.info("Processing experiment", experiment_id="exp-789")
# Logs: {..., "request_id": "req-123", "user_id": "user-456", "experiment_id": "exp-789"}

logger.clear_context()
```

#### Log Execution Time
```python
from app.core.structured_logging import log_execution_time

@log_execution_time(logger)
async def evaluate_batch(items):
    # Your code here
    pass

# Automatically logs: function, duration_seconds, status
```

#### Request Logging
```python
from app.core.structured_logging import RequestLogger

req_logger = RequestLogger(logger)

await req_logger.log_request(
    method="POST",
    path="/experiments/run",
    status_code=200,
    duration=0.234,
    api_key_id="key-123"
)
```

---

## 7. Webhook Notifications & Integration

### Overview
Real-time notifications for system integration and monitoring.

### Features
- **Event Types**: Multiple webhooks for different events
- **Retry Logic**: Automatic retries with exponential backoff
- **Signature Verification**: HMAC signing support
- **Delivery Logs**: Track webhook delivery status
- **Multiple Endpoints**: Notify multiple systems

### Event Types Available
```
- EXPERIMENT_CREATED
- EXPERIMENT_COMPLETED
- EXPERIMENT_FAILED
- EVALUATION_STARTED
- EVALUATION_COMPLETED
- RESULTS_READY
- THRESHOLD_EXCEEDED
```

### Usage

#### Setup Webhook
```python
from app.services.webhooks import WebhookManager, EventType

webhook_manager = WebhookManager(
    timeout=30,
    max_retries=3
)
```

#### Register Webhook Endpoint
```python
# In your database
webhook = WebhookEndpoint(
    name="Slack Notifications",
    url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    events=json.dumps([
        EventType.EXPERIMENT_COMPLETED,
        EventType.RESULTS_READY
    ]),
    is_active=True
)
```

#### Dispatch Event
```python
from app.services.webhooks import WebhookEventBuilder

# When experiment completes
await webhook_manager.dispatch_webhook(
    event_type=EventType.EXPERIMENT_COMPLETED,
    experiment_id="exp-123",
    data=WebhookEventBuilder.experiment_completed(
        experiment_id="exp-123",
        mean_score=8.5,
        std_dev=0.8,
        item_count=100
    ),
    webhook_urls=["https://your-endpoint.com/webhook"]
)
```

#### Webhook Payload Example
```json
{
  "event_type": "experiment.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "experiment_id": "exp-123",
  "data": {
    "mean_score": 8.5,
    "std_dev": 0.8,
    "item_count": 100,
    "completed_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Performance Monitoring

### Database Index Optimization
New indexes for faster queries:
```sql
CREATE INDEX idx_evaluation_results_experiment_id ON evaluation_results(experiment_id);
CREATE INDEX idx_evaluation_items_experiment_id ON evaluation_items(experiment_id);
```

### Cache Hit Rate Monitoring
Monitor Redis cache effectiveness:
```python
# In your monitoring dashboard
cache_info = await cache.client.info('stats')
print(f"Cache hits: {cache_info['keyspace_hits']}")
print(f"Cache misses: {cache_info['keyspace_misses']}")
hit_rate = cache_info['keyspace_hits'] / (cache_info['keyspace_hits'] + cache_info['keyspace_misses'])
print(f"Hit rate: {hit_rate:.2%}")
```

---

## Configuration Reference

### Environment Variables
```
# Authentication
API_KEY_EXPIRATION_DAYS=365
DEFAULT_RATE_LIMIT=1000

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# Batch Processing
BATCH_SIZE=10
CONCURRENT_BATCHES=3
BATCH_TIMEOUT_SECONDS=30

# Logging
LOG_LEVEL=INFO
USE_JSON_LOGGING=true

# Webhooks
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=3
```

---

## Best Practices

### 1. API Key Management
- Rotate keys regularly (every 90 days)
- Use different keys for different environments
- Store keys securely (never in code)
- Monitor key usage for anomalies

### 2. Caching Strategy
- Cache experiment results (24 hour TTL)
- Cache metrics calculations (1 hour TTL)
- Invalidate on updates immediately
- Monitor cache hit rates

### 3. Batch Processing
- Adjust batch size based on memory availability
- Use appropriate concurrency levels
- Monitor timeout durations
- Track retry rates

### 4. Logging & Monitoring
- Include request IDs for tracing
- Log all API calls
- Alert on error rates
- Monitor Redis cache health

### 5. Webhook Integration
- Implement idempotent handlers
- Validate webhook signatures
- Log all deliveries
- Monitor endpoint availability

---

## Troubleshooting

### Redis Connection Issues
```python
# Check connection
async with RedisCache() as cache:
    try:
        await cache.connect()
        print("Redis connected")
    except Exception as e:
        print(f"Redis error: {e}")
        # Will fall back to non-cached mode
```

### Rate Limit Exceeded
```
If you receive: HTTP 429 Too Many Requests
- Check your API key's rate limit
- Implement backoff in your client
- Contact support to increase limits
```

### PDF Export Failures
```python
# Requires reportlab
# If PDF export fails:
pip install reportlab

# For advanced PDF features:
pip install reportlab[renderimage]
```

---

## API Endpoint Examples

### Create API Key (Admin only)
```bash
POST /api/admin/api-keys
{
  "name": "Production Key",
  "organization": "MyOrg",
  "rate_limit": 5000,
  "expires_at": "2025-01-15T00:00:00Z"
}
```

### Export Experiment Results
```bash
GET /api/experiments/{experiment_id}/export?format=pdf
# Returns PDF file

GET /api/experiments/{experiment_id}/export?format=json
# Returns JSON data

GET /api/experiments/{experiment_id}/export?format=csv
# Returns CSV file
```

### Get Advanced Metrics
```bash
GET /api/experiments/{experiment_id}/metrics/advanced
# Returns:
{
  "mean_score": 8.5,
  "confidence_interval_95": [8.2, 8.8],
  "percentile_95": 9.2,
  "cohens_d": 0.45
}
```

### Register Webhook
```bash
POST /api/webhooks
{
  "name": "Slack",
  "url": "https://hooks.slack.com/...",
  "events": ["experiment.completed", "results.ready"]
}
```

---

## Summary

These advanced features position your LLM EaaS platform for:
- **Security**: API key authentication and rate limiting
- **Reliability**: Batch processing with retries and timeouts
- **Performance**: Redis caching and optimized queries
- **Insights**: Advanced statistics and comparisons
- **Integration**: Webhooks and multi-format exports
- **Observability**: Structured logging and monitoring

All features are backward compatible and can be adopted incrementally.
