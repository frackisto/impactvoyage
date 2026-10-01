# Image de production Next.js (sortie « standalone »), en trois étapes.

FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
# Variables publiques figées au build (incluses dans le code navigateur : aucun secret).
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
# Adresse interne du backend : sert aussi au relais /media/*, figé au build.
ARG API_URL=http://backend:8000/api/v1
# Serveur des médias du relais /media/* (vide : Django ; en production : Nginx).
ARG MEDIA_ORIGIN=
# Clé publique du widget anti-robot Cloudflare Turnstile (vide : widget absent).
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY=
# Recette : true interdit l'indexation (robots.txt figé au build).
ARG SEO_NOINDEX=false
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    API_URL=$API_URL \
    MEDIA_ORIGIN=$MEDIA_ORIGIN \
    NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY \
    SEO_NOINDEX=$SEO_NOINDEX
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
# Utilisateur sans privilèges : le serveur n'écrit que dans .next (cache des images).
RUN addgroup -S nodejs && adduser -S nextjs -G nodejs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
