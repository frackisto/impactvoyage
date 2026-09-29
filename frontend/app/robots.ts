import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/seo";

/**
 * robots.txt (CdC § 27). Les pages de résultats de recherche et les pages
 * personnelles (suivi de devis et de réservation, avec leur lien secret) ne
 * sont pas explorées. En recette (SEO_NOINDEX=true), rien n'est exploré.
 * Lu à chaque demande : le réglage vaut au démarrage du serveur, pas au build.
 */
export const dynamic = "force-dynamic";

const PRIVATE_PATHS = ["/recherche", "/reservation", "/devis/"];

export default function robots(): MetadataRoute.Robots {
  if (process.env.SEO_NOINDEX === "true") {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", "/admin", ...PRIVATE_PATHS, ...PRIVATE_PATHS.map((path) => `/en${path}`)],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
