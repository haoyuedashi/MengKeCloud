#!/usr/bin/env sh
set -e

echo "[api] waiting 2s for database..."
sleep 2

echo "[api] running migrations..."
alembic upgrade head

echo "[api] bootstrapping admin account..."
python scripts/bootstrap-admin.py

echo "[api] starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
