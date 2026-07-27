#!/bin/bash
set -e

# Backup do Postgres freela_food
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="freela_food_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Backing up freela_food database..."
docker exec $(docker ps -qf name=freela_food_postgres | head -1) \
  pg_dump -U freela -d freela_food \
  | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup saved: ${BACKUP_DIR}/${FILENAME}"
ls -lh "${BACKUP_DIR}/${FILENAME}"

# Manter últimos 7 backups
cd "$BACKUP_DIR" && ls -tp | grep -v '/$' | tail -n +8 | xargs -r rm --
echo "Old backups cleaned (keeping last 7)"
