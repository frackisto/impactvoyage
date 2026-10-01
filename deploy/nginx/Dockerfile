# Nginx de production (Phase 24, architecture § 15) : TLS, HSTS, limitation de débit,
# médias servis directement, relais vers Next.js, Django et Umami.
FROM nginx:1.30-alpine

# openssl : certificat autosigné provisoire tant que Let's Encrypt n'a pas répondu.
RUN apk add --no-cache openssl \
    && rm /etc/nginx/conf.d/default.conf \
    && mkdir -p /etc/nginx/certs

# Seules ces variables sont remplacées dans les gabarits : les variables de Nginx
# ($host, $remote_addr...) restent intactes.
ENV NGINX_ENVSUBST_FILTER="^(SITE_DOMAIN|SITE_ALIASES|API_DOMAIN|STATS_DOMAIN)$" \
    CERT_NAME=impactvoyage

COPY templates/ /etc/nginx/templates/
COPY snippets/ /etc/nginx/snippets/
COPY html/ /usr/share/nginx/html/errors/
COPY entrypoint.d/ /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/*.sh
