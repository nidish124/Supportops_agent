#!/usr/bin/env bash
set -e

if [ -z "$SMOKE_TEST_URL" ]; then
  echo "SMOKE_TEST_URL not set"
  exit 1
fi

python scripts/smoke_test.py "$SMOKE_TEST_URL"
