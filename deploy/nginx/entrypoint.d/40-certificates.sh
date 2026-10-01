#!/bin/sh
# Certificat TLS de Nginx (Phase 24).
#
# Nginx lit /etc/nginx/certs/, copie du certificat Let's Encrypt (volume partagé avec le
# service certbot, en lecture seule). Tant qu'il n'existe pas, un certificat autosigné
# permet de démarrer : le port 80 répond alors au défi de Let's Encrypt. Ensuite, chaque
# minute, un certificat nouveau ou renouvelé est copié puis chargé (nginx -s reload).
set -eu

live="/etc/letsencrypt/live/${CERT_NAME}"
certs=/etc/nginx/certs

install_certificate() {
    cp -L "$live/fullchain.pem" "$certs/fullchain.pem.new"
    cp -L "$live/privkey.pem" "$certs/privkey.pem.new"
    chmod 600 "$certs/privkey.pem.new"
    mv "$certs/fullchain.pem.new" "$certs/fullchain.pem"
    mv "$certs/privkey.pem.new" "$certs/privkey.pem"
}

if [ -f "$live/fullchain.pem" ]; then
    install_certificate
    echo "$0: certificat Let's Encrypt « ${CERT_NAME} » chargé."
elif [ ! -f "$certs/fullchain.pem" ]; then
    openssl req -x509 -nodes -newkey rsa:2048 -days 7 -subj "/CN=${SITE_DOMAIN}" \
        -keyout "$certs/privkey.pem" -out "$certs/fullchain.pem" 2>/dev/null
    chmod 600 "$certs/privkey.pem"
    echo "$0: certificat autosigné provisoire, en attente de Let's Encrypt."
fi

(
    while sleep 60; do
        if [ -f "$live/fullchain.pem" ] && ! cmp -s "$live/fullchain.pem" "$certs/fullchain.pem"; then
            install_certificate && nginx -s reload && echo "Nouveau certificat TLS chargé."
        fi
    done
) &
