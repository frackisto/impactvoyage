#!/bin/sh
# Restauration d'une base depuis une sauvegarde : la base actuelle est REMPLACÉE.
# Arrêter d'abord les services qui l'utilisent (voir DEPLOIEMENT.md, « Restaurer ») :
#   docker compose -f docker-compose.prod.yml --env-file .env.prod exec backup \
#     sh /opt/backup/restore.sh 2026-10-01_0230 voyage_db
[ "$(id -u)" = 0 ] && exec su-exec postgres sh "$0" "$@"
set -eu

if [ $# -ne 2 ]; then
    echo "Usage : restore.sh <dossier de sauvegarde, ex. 2026-10-01_0230> <base, ex. voyage_db>" >&2
    exit 2
fi
dir="/backups/$1"
db=$2
dump="$dir/$db.dump"
if [ ! -f "$dump" ]; then
    echo "Sauvegarde introuvable : $dump" >&2
    exit 1
fi
if ! (cd "$dir" && grep "  $db.dump\$" SHA256SUMS | sha256sum -c -s); then
    echo "Empreinte SHA-256 incorrecte : $dump est endommagé." >&2
    exit 1
fi

# Même propriétaire qu'avant (umami pour la base d'Umami).
owner=$(echo "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = :'db'" \
    | psql -tA -v db="$db" postgres)
owner=${owner:-$PGUSER}

dropdb --if-exists --force "$db"
createdb --owner "$owner" "$db"
pg_restore --no-owner --role "$owner" --exit-on-error --dbname "$db" "$dump"
echo "Base $db restaurée depuis $dump (propriétaire : $owner)."
