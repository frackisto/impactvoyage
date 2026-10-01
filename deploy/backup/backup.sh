#!/bin/sh
# Sauvegarde (Phase 24) : bases PostgreSQL (pg_dump, format compressé) et médias téléversés,
# dans /backups/AAAA-MM-JJ_HHMM/ avec leurs empreintes SHA-256 (SHA256SUMS). Lancée chaque
# nuit par scheduler.sh ; à la demande :
#   docker compose -f docker-compose.prod.yml --env-file .env.prod exec backup sh /opt/backup/backup.sh
[ "$(id -u)" = 0 ] && exec su-exec postgres sh "$0" "$@"
set -eu

stamp=$(date -u +%Y-%m-%d_%H%M)
target="/backups/$stamp"
work="/backups/.en-cours-$stamp"
rm -rf "$work"
mkdir -p "$work"

for db in $BACKUP_DATABASES; do
    pg_dump --format=custom --file "$work/$db.dump" "$db"
done
tar -czf "$work/media.tar.gz" -C /srv/media .
(cd "$work" && sha256sum -- * > SHA256SUMS)
rm -rf "$target"
mv "$work" "$target"
echo "Sauvegarde $target terminée ($(du -sh "$target" | cut -f1))."

# Conservation, d'après la date du dossier : bases BACKUP_RETENTION_DAYS jours ; archives des
# médias (complètes, donc volumineuses) MEDIA_BACKUP_RETENTION_DAYS jours.
days_ago() {
    date -u -d "@$(( $(date -u +%s) - $1 * 86400 ))" +%Y-%m-%d
}
keep_from=$(days_ago "$BACKUP_RETENTION_DAYS")
keep_media_from=$(days_ago "$MEDIA_BACKUP_RETENTION_DAYS")
for dir in /backups/20*; do
    [ -d "$dir" ] || continue
    day=$(basename "$dir" | cut -d_ -f1)
    if expr "$day" \< "$keep_from" > /dev/null; then
        rm -rf "$dir"
    elif expr "$day" \< "$keep_media_from" > /dev/null; then
        rm -f "$dir/media.tar.gz"
    fi
done
# Sauvegardes interrompues (arrêt du serveur pendant l'écriture).
find /backups -mindepth 1 -maxdepth 1 -type d -name '.en-cours-*' -mmin +720 -exec rm -rf {} +
