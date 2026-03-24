# Quick Integration Guide - Advanced Features

## 🚀 5-Minute Setup for New Features

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start Redis (Optional but Recommended)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Using Homebrew on macOS
brew install redis
redis-server
```

### Step 3: Configure Environment
```bash
# Edit your .env file
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
API_KEY_EXPIRATION_DAYS=365
DEFAULT_RATE_LIMIT=1000
LOG_LEVEL=INFO
USE_JSON_LOGGING=true
```

### Step 4: Add to `app/main.py`
```python
from fastapi import FastAPI, Depends
from app.core.auth import check_rate_limit, verify_api_key
from app.core.cache import RedisCache
from app.core.structured_logging import setup_structured_logging

app = FastAPI()

# Setup structured logging
logger = setup_structured_logging("llm_eaas")

# Initialize Redis cache
cache = RedisCache()

@app.on_event("startup")
async def startup():
    await cache.connect()

@app.on_event("shutdown")
async def shutdown():
    await cache.disconnect()

# Protected endpoint with rate limiting
@app.get("/api/experiments/{id}")
async def get_experiment(
    id: str,
    api_key = Depends(check_rate_limit)  # Adds auth + rate limiting
):
    return {"experiment_id": id, "api_key": api_key.name}
```

---

## 🔐 API Authentication Setup

### Create an API Key
```python
from app.core.auth import generate_api_key, hash_api_key
from app.models.api_key_models import APIKey
from uuid import uuid4

# Generate new key
plain_key = generate_api_key()  # sk_xxxxx...
key_hash = hash_api_key(plain_key)

# Store in database
api_key = APIKey(
    id=uuid4(),
    name="Production API",
    key_hash=key_hash,
    organization="MyOrg",
    is_active=True,
    rate_limit=5000
)
session.add(api_key)
await session.commit()

print(f"API Key (save this): {plain_key}")
```

### Use API Key in Requests
```bash
curl -H "X-API-Key: sk_xxxxx" \
  http://localhost:8000/api/experiments
```

---

## 📊 Advanced Metrics

### Calculate Stats
```python
from app.services.advanced_metrics import calculate_advanced_metrics

scores = [8.5, 9.0, 7.5, 8.8, 9.2]

metrics = calculate_advanced_metrics(
    scores=scores,
    safety_failures=0,
    total_items=5
)

print(f"Mean: {metrics.mean_score}")
print(f"P95: {metrics.percentile_95}")
print(f"95% CI: {metrics.confidence_interval_95}")
```

### Compare Two Experiments
```python
from app.services.advanced_metrics import compare_distributions

results = compare_distributions(
    scores_1=[8.5, 9.0, 7.5],
    scores_2=[7.2, 7.8, 8.1]
)

print(f"Cohen's d: {results['cohens_d']}")
print(f"Significant: {results['t_test']['significant']}")
```

---

## ⚡ Caching

### Cache Metrics
```python
from app.core.cache import RedisCache, CachedMetricsService

cache = RedisCache()
await cache.connect()

metrics_service = CachedMetricsService(cache)

# Get user-friendly name
await metrics_service.set_metrics(
    experiment_id="exp-123",
    metrics={"mean": 8.5, "std_dev": 0.8},
    ttl=3600  # 1 hour
)

# Retrieve
cached_metrics = await metrics_service.get_metrics("exp-123")
if cached_metrics:
    print("From cache:", cached_metrics)
```

---

## 📦 Batch Processing

### Process Large Datasets
```python
from app.services.batch_processing import BatchProcessor, BatchConfig

config = BatchConfig(batch_size=10, concurrent_batches=3)
processor = BatchProcessor(config)

async def evaluate_item(item):
    # Your evaluation logic
    return await llm_client.evaluate(item)

result = await processor.process_items(
    experiment_id=exp_id,
    session=session,
    process_fn=evaluate_item,
    batch_result=BatchResult(total_items=0, successful=0, failed=0, errors=[])
)

print(f"Success: {result.successful}/{result.total_items}")
```

---

## 📄 Export Results

### Export to Multiple Formats
```python
from app.services.export_service import ExperimentExporter

exporter = ExperimentExporter()

# JSON
json_str = exporter.to_json(experiment_data, results)

# CSV
csv_str = exporter.to_csv(experiment_data, results)

# PDF
pdf_bytes = exporter.to_pdf(experiment_data, results)

# HTML
html_str = exporter.to_html(experiment_data, results)

# Save to file
with open("results.pdf", "wb") as f:
    f.write(pdf_bytes)
```

---

## 🔔 Webhooks

### Register Webhook
```python
from app.services.webhooks import WebhookManager, EventType

manager = WebhookManager()

# Dispatch event
await manager.dispatch_webhook(
    event_type=EventType.EXPERIMENT_COMPLETED,
    experiment_id="exp-123",
    data={
        "mean_score": 8.5,
        "std_dev": 0.8,
        "completed_at": "2024-01-15T10:30:00Z"
    },
    webhook_urls=[
        "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "https://your-api.com/webhook/evaluation"
    ]
)
```

### Webhook Payload Received
```json
{
  "event_type": "experiment.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "experiment_id": "exp-123",
  "data": {
    "mean_score": 8.5,
    "std_dev": 0.8,
    "completed_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## 📝 Structured Logging

### Setup
```python
from app.core.structured_logging import (
    setup_structured_logging,
    StructuredLogger,
    log_execution_time
)

logger = setup_structured_logging("my_app")

# Decorator usage
@log_execution_time(logger)
async def evaluate_items(items):
    # Logs execution time automatically
    return await process(items)

# With context
struct_logger = StructuredLogger(logger)
struct_logger.set_context(request_id="req-123")
struct_logger.info("Processing", experiment_id="exp-456")
```

**Output**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "name": "my_app",
  "levelname": "INFO",
  "message": "Processing",
  "request_id": "req-123",
  "experiment_id": "exp-456"
}
```

---

## ✅ Complete Example: Protected & Cached Endpoint

```python
from fastapi import FastAPI, Depends
from app.core.auth import check_rate_limit
from app.core.cache import CachedMetricsService, RedisCache
from app.services.advanced_metrics import calculate_advanced_metrics
from app.core.structured_logging import log_execution_time
import logging

app = FastAPI()
cache = RedisCache()
logger = logging.getLogger("app")

@app.on_event("startup")
async def startup():
    await cache.connect()

@app.get("/experiments/{exp_id}/metrics")
@log_execution_time(logger)
async def get_metrics(
    exp_id: str,
    api_key = Depends(check_rate_limit),
    cache_service = Depends(lambda: CachedMetricsService(cache))
):
    # Check cache
    cached = await cache_service.get_metrics(exp_id)
    if cached:
        return {"source": "cache", "data": cached}
    
    # Calculate if not cached
    scores = [8.5, 9.0, 7.5, 8.8, 9.2]
    metrics = calculate_advanced_metrics(scores)
    
    # Cache for 1 hour
    await cache_service.set_metrics(
        exp_id, 
        {
            "mean": metrics.mean_score,
            "std_dev": metrics.std_dev,
            "p95": metrics.percentile_95
        },
        ttl=3600
    )
    
    return {"source": "calculated", "data": metrics}
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Redis Connection Error
```
ERROR: Connection refused
```
**Solution**: Start Redis
```bash
redis-server  # or docker run -d -p 6379:6379 redis:latest
```

### Issue 2: API Key Not Recognized
```
ERROR: Invalid or expired API key
```
**Solution**: Verify key hash in database
```sql
SELECT id, name, is_active, expires_at FROM api_keys 
WHERE is_active = true AND (expires_at IS NULL OR expires_at > NOW());
```

### Issue 3: Batch Processing Timeout
```
ERROR: Processing timeout for item
```
**Solution**: Increase timeout in config
```python
config = BatchConfig(timeout_per_item=60)  # 60 seconds
```

### Issue 4: PDF Export Fails
```
ERROR: reportlab not installed
```
**Solution**: Install reportlab
```bash
pip install reportlab
```

---

## 📊 Monitoring Checklist

- [ ] Redis running and accessible
- [ ] API keys created and tested
- [ ] Logs being generated in JSON format
- [ ] Cache hit rate > 50% (check Redis INFO)
- [ ] Batch processing succeeds for sample data
- [ ] Webhooks configured and tested
- [ ] Export functions generating files
- [ ] Advanced metrics calculating correctly

---

## 🎯 Testing

```python
# Test API key authentication
async def test_api_key():
    key = generate_api_key()
    # Store hash in db...
    # Call endpoint with key in header
    
# Test caching
async def test_cache():
    cache = RedisCache()
    await cache.connect()
    await cache.set("test", {"value": 123})
    result = await cache.get("test")
    assert result["value"] == 123

# Test advanced metrics
def test_metrics():
    scores = [8.5, 9.0, 7.5]
    m = calculate_advanced_metrics(scores)
    assert m.mean_score == 8.33
    assert m.percentile_95 >= 8.5

# Test batch processing
async def test_batch():
    config = BatchConfig(batch_size=2)
    processor = BatchProcessor(config)
    # Process test items...

# Test export
def test_export():
    exporter = ExperimentExporter()
    json_str = exporter.to_json({}, [])
    assert json_str is not None
```

---

## 📚 Detailed Documentation

For comprehensive documentation, see:
- **[ADVANCED_FEATURES_GUIDE.md](../ADVANCED_FEATURES_GUIDE.md)** - Complete reference
- **[IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)** - Feature overview
- **API_DOCUMENTATION.md** - API endpoints

---

**Ready to go!** 🚀

Start with authentication, add caching, then webhooks. All features work independently.
