#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-}"
SAMPLE_CSV="${2:-sample_data.csv}"
RUN_EVALUATION="${RUN_EVALUATION:-1}"

if [[ -z "$BASE_URL" ]]; then
  echo "Usage: ./post_deploy_smoke_test.sh <BASE_URL> [SAMPLE_CSV_PATH]"
  echo "Example: ./post_deploy_smoke_test.sh https://llm-eaas-backend.onrender.com"
  echo "Set RUN_EVALUATION=0 to skip expensive LLM judging step."
  exit 1
fi

if [[ ! -f "$SAMPLE_CSV" ]]; then
  echo "[FAIL] Sample CSV not found: $SAMPLE_CSV"
  exit 1
fi

BASE_URL="${BASE_URL%/}"

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
  exit 1
}

extract_experiment_id() {
  local json="$1"
  printf '%s' "$json" | sed -n 's/.*"experiment_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

request_with_status() {
  local method="$1"
  local url="$2"
  local body_file="$3"
  shift 3

  local status
  status=$(curl -sS -X "$method" "$url" -o "$body_file" -w "%{http_code}" "$@") || return 1
  printf '%s' "$status"
}

echo "Running post-deploy smoke test against: $BASE_URL"

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

health_body="$tmp_dir/health.json"
health_status=$(request_with_status "GET" "$BASE_URL/health" "$health_body") || fail "Unable to reach /health"
if [[ "$health_status" != "200" ]]; then
  fail "/health returned HTTP $health_status: $(cat "$health_body")"
fi
pass "Health endpoint is reachable"

root_body="$tmp_dir/root.json"
root_status=$(request_with_status "GET" "$BASE_URL/" "$root_body") || fail "Unable to reach root endpoint"
if [[ "$root_status" != "200" ]]; then
  fail "Root endpoint returned HTTP $root_status: $(cat "$root_body")"
fi
pass "Root endpoint is reachable"

upload_body="$tmp_dir/upload.json"
upload_status=$(request_with_status "POST" "$BASE_URL/experiments/upload" "$upload_body" -F "file=@$SAMPLE_CSV") || fail "Upload request failed"
if [[ "$upload_status" != "200" ]]; then
  fail "Upload returned HTTP $upload_status: $(cat "$upload_body")"
fi

upload_response=$(cat "$upload_body")
experiment_id=$(extract_experiment_id "$upload_response")
if [[ -z "$experiment_id" ]]; then
  fail "Could not parse experiment_id from upload response: $upload_response"
fi
pass "Upload succeeded (experiment_id=$experiment_id)"

if [[ "$RUN_EVALUATION" == "1" ]]; then
  run_payload="$tmp_dir/run_payload.json"
  cat > "$run_payload" <<EOF
{
  "experiment_id": "$experiment_id",
  "rubric": {
    "factuality": {"min": 0, "max": 5},
    "relevance": {"min": 0, "max": 5},
    "clarity": {"min": 0, "max": 5},
    "safety": {"type": "pass_fail"}
  },
  "temperature": 0.2
}
EOF

  run_body="$tmp_dir/run.json"
  run_status=$(request_with_status "POST" "$BASE_URL/experiments/run" "$run_body" -H "Content-Type: application/json" --data-binary "@$run_payload") || fail "Run request failed"
  if [[ "$run_status" != "200" ]]; then
    fail "Run returned HTTP $run_status: $(cat "$run_body")"
  fi

  run_response=$(cat "$run_body")
  if ! printf '%s' "$run_response" | grep -q '"status"'; then
    fail "Run response missing status field: $run_response"
  fi
  pass "Evaluation run endpoint succeeded"
else
  echo "[SKIP] Evaluation run skipped (RUN_EVALUATION=$RUN_EVALUATION)"
fi

experiment_body="$tmp_dir/experiment.json"
experiment_status=$(request_with_status "GET" "$BASE_URL/experiments/$experiment_id" "$experiment_body") || fail "Get experiment request failed"
if [[ "$experiment_status" != "200" ]]; then
  fail "Get experiment returned HTTP $experiment_status: $(cat "$experiment_body")"
fi
pass "Experiment details endpoint succeeded"

if [[ "$RUN_EVALUATION" == "1" ]]; then
  gate_body="$tmp_dir/ci_gate.json"
  gate_status=$(request_with_status "GET" "$BASE_URL/experiments/$experiment_id/ci-gate" "$gate_body") || fail "CI gate request failed"
  if [[ "$gate_status" != "200" ]]; then
    fail "CI gate returned HTTP $gate_status: $(cat "$gate_body")"
  fi
  pass "CI gate endpoint succeeded"
else
  echo "[SKIP] CI gate skipped because RUN_EVALUATION=$RUN_EVALUATION"
fi

echo
echo "Smoke test completed successfully."
echo "Experiment ID: $experiment_id"
