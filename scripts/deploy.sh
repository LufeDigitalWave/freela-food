#!/bin/bash
set -e

echo "=== freela-food deploy ==="
echo "1. Building images..."
docker compose -f docker-compose.deploy.yml build

echo "2. Running migrations..."
docker compose -f docker-compose.deploy.yml run --rm api alembic upgrade head

echo "3. Starting services..."
docker compose -f docker-compose.deploy.yml up -d

echo "4. Waiting for health..."
sleep 10
curl -sf http://localhost/health || echo "WARNING: health check failed"

echo "=== Deploy complete ==="
docker compose -f docker-compose.deploy.yml ps
