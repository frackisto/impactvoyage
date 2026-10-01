import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

/**
 * Origine de Django vue par le serveur Next.js. Figée au build : les réécritures
 * (rewrites) sont compilées dans l'application.
 */
const backendOrigin = new URL(process.env.API_URL ?? "http://localhost:8000/api/v1").origin;
/**
 * Serveur des médias pour le relais /media/* (optimisation des images par next/image).
 * Django ne sert les médias qu'en développement : en production, c'est Nginx, sur son
 * port interne (MEDIA_ORIGIN=http://nginx:8080, docker-compose.prod.yml).
 */
const mediaOrigin = process.env.MEDIA_ORIGIN ? new URL(process.env.MEDIA_ORIGIN).origin : backendOrigin;

/**
 * En-têtes de sécurité de toutes les réponses (Phase 23). La CSP des pages, qui porte
 * un nonce propre à chaque réponse, est posée par proxy.ts ; les routes /api (JSON)
 * n'ont rien à charger ni à afficher. HSTS seulement si le site est servi en HTTPS.
 */
const https = (process.env.NEXT_PUBLIC_SITE_URL ?? "").startsWith("https://");
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  ...(https ? [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains; preload" }] : []),
];
const apiHeaders = [
  { key: "Content-Security-Policy", value: "default-src 'none'; frame-ancestors 'none'" },
  { key: "Cache-Control", value: "no-store" },
];

const nextConfig: NextConfig = {
  // Image Docker autonome et légère (architecture § 15).
  output: "standalone",
  poweredByHeader: false,
  images: {
    formats: ["image/avif", "image/webp"],
    // Seules les images du site et les médias Django sont optimisées.
    localPatterns: [{ pathname: "/brand/**" }, { pathname: "/images/**" }, { pathname: "/media/**" }],
  },
  // Photos du catalogue : /media/* relayé vers Django, ou Nginx en production (voir
  // lib/media.ts) ; les navigateurs, eux, les reçoivent directement de Nginx.
  async rewrites() {
    return [{ source: "/media/:path*", destination: `${mediaOrigin}/media/:path*` }];
  },
  // Pas de redirection /admin vers le backoffice : son adresse, non standard en
  // production (ADMIN_URL_PATH), ne doit apparaître nulle part sur le site.
  async headers() {
    return [
      { source: "/:path*", headers: securityHeaders },
      { source: "/api/:path*", headers: apiHeaders },
    ];
  },
};

export default withNextIntl(nextConfig);
