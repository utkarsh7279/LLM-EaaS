#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${1:-}"
FRONTEND_URL="${2:-}"
SAMPLE_CSV="${3:-sample_data.csv}"
RUN_EVALUATION="${RUN_EVALUATION:-1}"

if [[ -z "$BACKEND_URL" || -z "$FRONTEND_URL" ]]; then
  echo "Usage: ./verify_production_deploy.sh <BACKEND_URL> <FRONTEND_URL> [SAMPLE_CSV_PATH]"
  echo "Example: ./verify_production_deploy.sh https://llm-eaas.onrender.com https://frontend-chi-flame-36.vercel.app"
  echo "Set RUN_EVALUATION=0 to skip expensive LLM judging step."
  exit 1
fi

if [[ ! -f "$SAMPLE_CSV" ]]; then
  echo "[FAIL] Sample CSV not found: $SAMPLE_CSV"
  exit 1
fi

if [[ ! -x "./post_deploy_smoke_test.sh" ]]; then
  chmod +x ./post_deploy_smoke_test.sh
fi

BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"
BACKEND_HOST=$(printf '%s' "$BACKEND_URL" | sed -E 's#^https?://##')

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
  exit 1
}

echo "Running production deployment verification"
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo

frontend_status=$(curl -sS -o "$tmp_dir/frontend_home.html" -w "%{http_code}" "$FRONTEND_URL") || fail "Unable to reach frontend URL"
if [[ "$frontend_status" != "200" ]]; then
  fail "Frontend returned HTTP $frontend_status"
fi
pass "Frontend homepage is reachable"

# Pull all script chunks that the current HTML references, then inspect their contents.
grep -Eo "/_next/static/chunks/[^\" ]+\\.js" "$tmp_dir/frontend_home.html" | sort -u > "$tmp_dir/chunks.txt"
if [[ ! -s "$tmp_dir/chunks.txt" ]]; then
  fail "No Next.js chunk references found in frontend HTML"
fi

while IFS= read -r chunk; do
  curl -sS "$FRONTEND_URL$chunk" >> "$tmp_dir/all_chunks.js"
done < "$tmp_dir/chunks.txt"

if grep -q "localhost:8000" "$tmp_dir/all_chunks.js"; then
  fail "Frontend bundle still references localhost:8000"
fi
pass "Frontend bundle does not reference localhost"

if ! grep -q "$BACKEND_HOST" "$tmp_dir/all_chunks.js"; then
  fail "Frontend bundle does not reference expected backend host: $BACKEND_HOST"
fi
pass "Frontend bundle references expected backend host"

RUN_EVALUATION="$RUN_EVALUATION" ./post_deploy_smoke_test.sh "$BACKEND_URL" "$SAMPLE_CSV"
pass "Backend smoke test completed"

echo
echo "All production verification checks passed."
