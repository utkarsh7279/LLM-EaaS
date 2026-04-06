#!/usr/bin/env bash
set -euo pipefail

# Lightweight secret-pattern scan over tracked files.
# Uses conservative rules and path exclusions to avoid noise from docs/examples.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

EXCLUDE_PATHS_REGEX='(\.venv/|frontend/node_modules/|frontend/\.next/|backend/venv/|docs/|\.md$|\.lock$)'

# Regexes that are strong indicators of leaked credentials.
PATTERNS='
-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----
AKIA[0-9A-Z]{16}
ASIA[0-9A-Z]{16}
sk-[A-Za-z0-9_-]{20,}
gsk_[A-Za-z0-9_-]{20,}
xox[baprs]-[A-Za-z0-9-]{10,}
ghp_[A-Za-z0-9]{30,}
github_pat_[A-Za-z0-9_]{20,}
postgresql(\+asyncpg)?://[^[:space:]/:@]+:[^[:space:]@]+@
'

# Lines containing these tokens are treated as examples/placeholders and ignored.
ALLOWLIST_TOKENS_REGEX='(<password>|YOUR_|YOUR-|PASSWORD|password123|username:password|USER:PASSWORD|postgres:postgres|example|xxxxx|localhost|SECURE_)'

FAIL=0
hits_file="$(mktemp)"
trap 'rm -f "$hits_file"' EXIT

printf '%s\n' "$PATTERNS" | while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  git grep -nEI -e "$pattern" -- . || true
done > "$hits_file"

while IFS= read -r hit; do
  [[ -z "$hit" ]] && continue
  hit_path="${hit%%:*}"
  if printf '%s\n' "$hit_path" | grep -Eq "$EXCLUDE_PATHS_REGEX"; then
    continue
  fi
  if printf '%s' "$hit" | grep -Eiq "$ALLOWLIST_TOKENS_REGEX"; then
    continue
  fi
  echo "[SECRET-HIT] $hit"
  FAIL=1
done < "$hits_file"

if [[ "$FAIL" -ne 0 ]]; then
  echo
  echo "Secret scan failed. Remove secrets or move them to environment variables."
  exit 1
fi

echo "Secret scan passed."
