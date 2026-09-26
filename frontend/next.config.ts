import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

/**
 * Origine de Django vue par le serveur Next.js. Figée au build : les réécritures
 * (rewrites) sont compilées dans l'application.
 */
const backendOrigin = new URL(process.env.API_URL ?? "http://localhost:8000/api/v1").origin;

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
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
  // Photos du catalogue : /media/* relayé vers Django (voir lib/media.ts).
  async rewrites() {
    return [{ source: "/media/:path*", destination: `${backendOrigin}/media/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default withNextIntl(nextConfig);
