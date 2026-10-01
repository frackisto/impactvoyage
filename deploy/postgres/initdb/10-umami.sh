#!/bin/sh
# Base et utilisateur d'Umami (mesure d'audience, Phase 24), à côté de la base du site.
# Exécuté automatiquement au premier démarrage de PostgreSQL (volume vide). Sur un volume
# existant, à lancer une fois (sans effet si tout existe déjà) :
#   docker compose -f docker-compose.prod.yml --env-file .env.prod exec db \
#     sh /docker-entrypoint-initdb.d/10-umami.sh
# (Pas de « set -u » : sans droit d'exécution, l'image source ce fichier dans son propre script.)
: "${UMAMI_DB_PASSWORD:?UMAMI_DB_PASSWORD est obligatoire}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v password="$UMAMI_DB_PASSWORD" <<'SQL'
SELECT 'CREATE ROLE umami LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'umami')\gexec
ALTER ROLE umami WITH LOGIN PASSWORD :'password';
SELECT 'CREATE DATABASE umami OWNER umami' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'umami')\gexec
SQL
echo "Base umami prête."
