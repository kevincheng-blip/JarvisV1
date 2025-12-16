#!/usr/bin/env bash
set -e

curl --max-time 2 -sS http://127.0.0.1:8000/api/v1/intelligence/status/latest \
| head -20 || echo "API server not running (expected if not started)"

