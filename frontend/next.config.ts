import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

/** Hôte public des médias Django (photos du catalogue), ex. http://localhost:8000. */
const mediaUrl = new URL(process.env.NEXT_PUBLIC_MEDIA_URL ?? "http://localhost:8000");

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
    remotePatterns: [
      {
        protocol: mediaUrl.protocol.replace(":", "") as "http" | "https",
        hostname: mediaUrl.hostname,
        port: mediaUrl.port,
        pathname: "/media/**",
      },
    ],
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default withNextIntl(nextConfig);
