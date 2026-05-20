#!/usr/bin/env bash
# Backup PostgreSQL (Neon) via pg_dump
# Usage : ./scripts/backup_db.sh
# Cron  : 0 3 * * * /path/to/project/scripts/backup_db.sh >> /var/log/lysangels_backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/lysangels}"
KEEP_DAYS="${KEEP_DAYS:-7}"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
FILENAME="lysangels_${TIMESTAMP}.dump"

# Charge DATABASE_URL depuis .env si pas déjà dans l'environnement
if [ -z "${DATABASE_URL:-}" ]; then
    ENV_FILE="$(dirname "$0")/../.env"
    if [ -f "$ENV_FILE" ]; then
        DATABASE_URL=$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d'=' -f2-)
    fi
fi

if [ -z "${DATABASE_URL:-}" ]; then
    echo "[$(date)] ERREUR : DATABASE_URL non définie." >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Démarrage du backup → ${BACKUP_DIR}/${FILENAME}"

pg_dump --format=custom --no-acl --no-owner "$DATABASE_URL" \
    --file="${BACKUP_DIR}/${FILENAME}"

SIZE=$(du -sh "${BACKUP_DIR}/${FILENAME}" | cut -f1)
echo "[$(date)] Backup terminé : ${FILENAME} (${SIZE})"

# Supprime les backups plus vieux que KEEP_DAYS jours
DELETED=$(find "$BACKUP_DIR" -name "lysangels_*.dump" -mtime "+${KEEP_DAYS}" -print -delete | wc -l)
[ "$DELETED" -gt 0 ] && echo "[$(date)] ${DELETED} ancien(s) backup(s) supprimé(s)"

echo "[$(date)] Backups disponibles : $(ls "$BACKUP_DIR"/lysangels_*.dump 2>/dev/null | wc -l)"
