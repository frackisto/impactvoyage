#!/bin/sh
# Planificateur du service « backup » (Phase 24, architecture § 7.1) : sauvegarde chaque
# jour à BACKUP_TIME (heure UTC, celle d'Abidjan) et test de restauration le 1er du mois.
if [ "$(id -u)" = 0 ]; then
    chown postgres:postgres /backups
    exec su-exec postgres sh "$0" "$@"
fi
set -u

echo "Sauvegardes quotidiennes à ${BACKUP_TIME} UTC dans /backups (bases : ${BACKUP_DATABASES})."
trap 'exit 0' TERM INT
done_today=""
while :; do
    today=$(date -u +%F)
    if [ "$(date -u +%H:%M)" = "$BACKUP_TIME" ] && [ "$done_today" != "$today" ]; then
        done_today=$today
        sh /opt/backup/backup.sh || echo "ÉCHEC de la sauvegarde du $today" >&2
        if [ "$(date -u +%d)" = "01" ]; then
            sh /opt/backup/restore-check.sh || echo "ÉCHEC du test de restauration du $today" >&2
        fi
    fi
    sleep 20 & wait $!
done
