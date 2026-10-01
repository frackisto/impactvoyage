#!/bin/sh
# Certificat Let's Encrypt de tous les domaines (Phase 24) : obtenu au premier passage,
# renouvelé moins de 30 jours avant son expiration, rien sinon. Nginx répond au défi
# (/.well-known/acme-challenge/, volume partagé) et charge le nouveau certificat de
# lui-même (deploy/nginx/entrypoint.d/40-certificates.sh).
set -u

if [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
    echo "LETSENCRYPT_EMAIL est vide : pas de certificat Let's Encrypt (certificat autosigné de Nginx)."
    exec sleep infinity
fi

domains="-d ${SITE_DOMAIN} -d ${API_DOMAIN} -d ${STATS_DOMAIN}"
for alias in ${SITE_ALIASES:-}; do
    domains="$domains -d $alias"
done
staging=""
[ "${LETSENCRYPT_STAGING:-0}" = "1" ] && staging="--staging"

trap 'exit 0' TERM INT
# Laisse à Nginx le temps de démarrer avant la première demande.
sleep 15 & wait $!
while :; do
    # shellcheck disable=SC2086
    if certbot certonly --webroot -w /var/www/certbot --cert-name "${CERT_NAME}" $domains \
        --email "${LETSENCRYPT_EMAIL}" --agree-tos --no-eff-email --non-interactive \
        --keep-until-expiring --expand $staging; then
        delay=12h
    else
        # Échec (DNS pas encore propagé, port 80 fermé...) : nouvel essai dans une heure,
        # sans dépasser le quota d'échecs de Let's Encrypt.
        delay=1h
    fi
    sleep "$delay" & wait $!
done
