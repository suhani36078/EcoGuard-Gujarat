#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_tests.sh — Run the full test suite
# Usage: ./scripts/run_tests.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Running backend tests"
cd "$ROOT_DIR"
python -m pytest tests/ -v --tb=short

echo ""
echo "==> Running frontend TypeScript check"
cd "$ROOT_DIR/frontend"
npx tsc --noEmit

echo ""
echo "✅ All checks passed!"
