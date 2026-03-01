#!/usr/bin/env bash
set -euo pipefail

export PERSONAOPS_STORE_BACKEND=postgres
export PERSONAOPS_POSTGRES_DSN=${PERSONAOPS_POSTGRES_DSN:-postgresql://personaops:personaops@localhost:55432/personaops}

echo "[postgres] applying schema"
psql "$PERSONAOPS_POSTGRES_DSN" -f implementation/sql/001_init.sql >/dev/null

echo "[postgres] running integration tests"
pytest -m integration -q

echo "[postgres] smoke test done"
