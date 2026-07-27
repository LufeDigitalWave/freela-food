#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file.sql.gz>"
  echo "Example: $0 ./backups/freela_food_20260724_120000.sql.gz"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: File not found: $BACKUP_FILE"
  exit 1
fi

echo "WARNING: This will DROP and recreate the freela_food database!"
read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

CONTAINER=$(docker ps -qf name=freela_food_postgres | head -1)

echo "Dropping and recreating database..."
docker exec "$CONTAINER" psql -U freela -d postgres -c "DROP DATABASE IF EXISTS freela_food;"
docker exec "$CONTAINER" psql -U freela -d postgres -c "CREATE DATABASE freela_food OWNER freela;"

echo "Restoring from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER" psql -U freela -d freela_food

echo "Restore complete!"
docker exec "$CONTAINER" psql -U freela -d freela_food -c "SELECT version_num FROM alembic_version;"
