# API Documentation

## Overview

The LLM Evaluation-as-a-Service (EaaS) API provides endpoints for managing LLM evaluation experiments with rubric-driven scoring, regression detection, and CI/CD integration.

**Base URL**: `http://localhost:8000`

**Authentication**: None (configure `ALLOWED_ORIGINS` for CORS)

---

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Description**: Simple health check to verify the API is running.

**Response**: 
```json
{
  "status": "ok"
}
```

**Status Code**: `200 OK`

---

### 2. Upload Experiment

**Endpoint**: `POST /experiments/upload`

**Description**: Upload a CSV dataset and create a new experiment.

**Request**:
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` (required): CSV file with columns: `prompt`, `model_output`, and optional `reference_output`

**CSV Format**:
```csv
prompt,model_output,reference_output
"How does photosynthesis work?","Photosynthesis converts sunlight into chemical energy...","Plants use sunlight to produce energy..."
"What is AI?","AI is intelligence demonstrated by machines...","AI is the simulation of human intelligence..."
```

**Response** (201 Created):
```json
{
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:
- `400 Bad Request`: Missing required columns, invalid file format, empty file
- `415 Unsupported Media Type`: Non-CSV file uploaded

**Example cURL**:
```bash
curl -X POST \
  -F "file=@sample_data.csv" \
  http://localhost:8000/experiments/upload
```

---

### 3. Run Experiment

**Endpoint**: `POST /experiments/run`

**Description**: Execute rubric-based evaluation for an experiment.

**Request**:
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
  "rubric": {
    "factuality": { "min": 0, "max": 5 },
    "relevance": { "min": 0, "max": 5 },
    "clarity": { "min": 0, "max": 5 },
    "safety": { "type": "pass_fail" }
  },
  "temperature": 0.2
}
```

**Rubric Field Types**:
- **Numeric**: Define with `min` and `max` values (e.g., 0-5 scale)
- **Binary/Pass-Fail**: Define with `type: "pass_fail"` or `type: "binary"`

**Response** (200 OK):
```json
{
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "metrics": {
    "mean_score": 4.31,
    "safety_fail_rate": 0.08,
    "std_dev": 0.52
  },
  "results": [
    {
      "item_id": "item-uuid-1",
      "rubric_scores": {
        "factuality": 4,
        "relevance": 5,
        "clarity": 4,
        "safety": "pass"
      },
      "overall_score": 4.33,
      "reasoning": "Response is factually accurate and relevant..."
    }
  ]
}
```

**Status**: `running` → `completed` or `failed`

**Error Responses**:
- `400 Bad Request`: Invalid experiment ID, invalid rubric JSON, no items found
- `404 Not Found`: Experiment does not exist

**Example cURL**:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
    "rubric": {
      "factuality": {"min": 0, "max": 5},
      "relevance": {"min": 0, "max": 5},
      "clarity": {"min": 0, "max": 5},
      "safety": {"type": "pass_fail"}
    },
    "temperature": 0.2
  }' \
  http://localhost:8000/experiments/run
```

---

### 4. Get Experiment

**Endpoint**: `GET /experiments/{experiment_id}`

**Description**: Retrieve experiment details with all evaluation results and aggregated metrics.

**Parameters**:
- `experiment_id` (path, required): UUID of the experiment

**Response** (200 OK):
```json
{
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "metrics": {
    "mean_score": 4.31,
    "safety_fail_rate": 0.08,
    "std_dev": 0.52
  },
  "results": [
    {
      "item_id": "item-uuid-1",
      "rubric_scores": {
        "factuality": 4,
        "relevance": 5,
        "clarity": 4,
        "safety": "pass"
      },
      "overall_score": 4.33,
      "reasoning": "Response is factually accurate and relevant..."
    }
  ]
}
```

**Experiment Status Values**:
- `created`: Experiment created but not yet evaluated
- `uploaded`: Dataset uploaded
- `running`: Evaluation in progress
- `completed`: Evaluation finished successfully
- `failed`: Evaluation failed

**Error Responses**:
- `404 Not Found`: Experiment does not exist

**Example cURL**:
```bash
curl http://localhost:8000/experiments/550e8400-e29b-41d4-a716-446655440000
```

---

### 5. Compare Experiments

**Endpoint**: `GET /experiments/compare`

**Description**: Compare two experiments and detect regression in scores.

**Query Parameters**:
- `baseline` (required): Experiment ID for baseline
- `candidate` (required): Experiment ID for candidate

**Response** (200 OK):
```json
{
  "baseline_experiment_id": "baseline-uuid",
  "candidate_experiment_id": "candidate-uuid",
  "regression_detected": false,
  "delta_mean_score": 0.15
}
```

**Fields**:
- `regression_detected`: `true` if drop > threshold (default 5%)
- `delta_mean_score`: Candidate score - Baseline score (positive = improvement)

**Error Responses**:
- `400 Bad Request`: Missing baseline or candidate ID, metrics not found
- `404 Not Found`: Experiment not found

**Example cURL**:
```bash
curl "http://localhost:8000/experiments/compare?baseline=baseline-uuid&candidate=candidate-uuid"
```

---

### 6. CI/CD Gate

**Endpoint**: `GET /experiments/{experiment_id}/ci-gate`

**Description**: Return CI/CD deployment decision based on regression check against baseline.

**Parameters**:
- `experiment_id` (path, required): UUID of the experiment to evaluate

**Response** (200 OK):
```json
{
  "experiment_id": "550e8400-e29b-41d4-a716-446655440000",
  "mean_score": 4.31,
  "regression_detected": false,
  "deployment_allowed": true
}
```

**Fields**:
- `deployment_allowed`: `true` if no regression detected
- `regression_detected`: `true` if score drop exceeds threshold

**Error Responses**:
- `400 Bad Request`: No baseline configured, metrics not found
- `404 Not Found`: Experiment not found

**Example cURL**:
```bash
curl http://localhost:8000/experiments/550e8400-e29b-41d4-a716-446655440000/ci-gate
```

---

## Request/Response Examples

### Complete Workflow

**Step 1: Upload Dataset**
```bash
curl -X POST -F "file=@sample_data.csv" http://localhost:8000/experiments/upload
```
Response:
```json
{"experiment_id": "exp-1"}
```

**Step 2: Run Evaluation**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "exp-1",
    "rubric": {
      "factuality": {"min": 0, "max": 5},
      "relevance": {"min": 0, "max": 5},
      "safety": {"type": "pass_fail"}
    }
  }' \
  http://localhost:8000/experiments/run
```

**Step 3: Get Results**
```bash
curl http://localhost:8000/experiments/exp-1
```

**Step 4: Compare with Baseline**
```bash
curl "http://localhost:8000/experiments/compare?baseline=baseline-exp&candidate=exp-1"
```

**Step 5: Check CI Gate**
```bash
curl http://localhost:8000/experiments/exp-1/ci-gate
```

---

## Error Handling

All errors return JSON with appropriate HTTP status codes:

```json
{
  "detail": "Error message describing the issue"
}
```

**Common Status Codes**:
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input or invalid state
- `404 Not Found`: Resource not found
- `415 Unsupported Media Type`: Invalid file type
- `500 Internal Server Error`: Server error

---

## Rubric Definition Guide

### Numeric Rubrics
```json
{
  "factuality": {
    "min": 0,
    "max": 5,
    "description": "How accurate is the information?"
  },
  "relevance": {
    "min": 0,
    "max": 10,
    "description": "How relevant is the response?"
  }
}
```

### Binary/Pass-Fail Rubrics
```json
{
  "safety": {
    "type": "pass_fail",
    "description": "Does the response meet safety standards?"
  },
  "contains_harmful_content": {
    "type": "binary",
    "description": "Is there harmful content?"
  }
}
```

### Mixed Rubric Example
```json
{
  "factuality": {"min": 0, "max": 5},
  "relevance": {"min": 0, "max": 5},
  "completeness": {"min": 0, "max": 3},
  "safety": {"type": "pass_fail"},
  "toxicity": {"type": "pass_fail"}
}
```

---

## Metrics Explanation

### Mean Score
Average of all overall scores in the experiment.
```
mean_score = sum(overall_scores) / count(overall_scores)
```

### Standard Deviation
Measures the spread of scores around the mean.
```
std_dev = sqrt(sum((score - mean)²) / count(scores))
```

### Safety Fail Rate
Percentage of items that failed safety checks.
```
safety_fail_rate = count(safety == "fail") / total_count
```

---

## Performance Considerations

- **Batch Size**: Evaluation is performed item-by-item. Large experiments (>1000 items) may take several minutes.
- **Timeout**: Default timeout is 60 seconds per LLM call.
- **Retry Logic**: Failed LLM responses are retried up to 2 times by default.
- **Temperature**: Lower values (0.0-0.3) increase consistency; higher values (0.7-1.0) increase creativity.

---

## Rate Limiting

No built-in rate limiting. Configure at reverse proxy or API gateway level as needed.

---

## Versioning

Current API version: `v1` (implicit in endpoints)

Future versions may be prefixed with `/v2/experiments/...`
