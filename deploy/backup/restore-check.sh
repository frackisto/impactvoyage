#!/bin/sh
# Test de restauration (architecture § 7.1) : la dernière sauvegarde est vérifiée
# (empreintes, archive des médias) puis la base du site est restaurée dans une base
# temporaire, interrogée et supprimée. Lancé le 1er de chaque mois par scheduler.sh ;
# à la demande :
#   docker compose -f docker-compose.prod.yml --env-file .env.prod exec backup sh /opt/backup/restore-check.sh
[ "$(id -u)" = 0 ] && exec su-exec postgres sh "$0" "$@"
set -eu

# Dossiers datés : le dernier dans l'ordre alphabétique est le plus récent.
latest=""
for dir in /backups/20*; do
    [ -d "$dir" ] && latest=$dir
done
if [ -z "$latest" ]; then
    echo "Aucune sauvegarde à vérifier dans /backups." >&2
    exit 1
fi
cd "$latest"
sha256sum -c -s SHA256SUMS
tar -tzf media.tar.gz > /dev/null

main_db=${BACKUP_DATABASES%% *}
for db in $BACKUP_DATABASES; do
    pg_restore --list "$db.dump" > /dev/null
done

scratch=restauration_test
export PGOPTIONS="-c client_min_messages=warning"
dropdb --if-exists "$scratch"
createdb "$scratch"
trap 'dropdb --if-exists "$scratch"' EXIT
pg_restore --no-owner --no-privileges --exit-on-error --dbname "$scratch" "$main_db.dump"
tables=$(psql -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'" "$scratch")
migrations=$(psql -tAc "SELECT count(*) FROM django_migrations" "$scratch")
echo "Test de restauration réussi ($latest) : $tables tables, $migrations migrations appliquées."
