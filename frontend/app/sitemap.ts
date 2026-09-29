import type { MetadataRoute } from "next";

import { routing } from "@/i18n/routing";
import { backendFetch } from "@/lib/api/backend";
import { absoluteUrl } from "@/lib/seo";
import type { components } from "@/types/api";

type SitemapData = components["schemas"]["Sitemap"];

/**
 * Plan du site (CdC § 27) : toutes les pages publiques, dans chaque langue, avec
 * leurs variantes hreflang. Les contenus viennent de Django (/seo/sitemap/) ;
 * l'étiquette « sitemap » est régénérée dès qu'un contenu est publié ou retiré.
 * Rendu à chaque demande : au build (Docker), Django n'est pas joignable.
 */
export const dynamic = "force-dynamic";

/** Pages fixes indexables (les listes filtrées et les pages privées ne le sont pas). */
const STATIC_PAGES = [
  "/", "/destinations", "/circuits/nationaux", "/circuits/internationaux", "/hotels",
  "/residences", "/vehicules", "/activites", "/evenements", "/offres", "/services", "/visa",
  "/transport", "/mediatheque", "/blog", "/a-propos", "/contact", "/devis",
  "/mentions-legales", "/confidentialite", "/conditions-generales",
];

const CONTINENTS = ["AFRIQUE", "EUROPE", "AMERIQUES", "ASIE", "MOYEN_ORIENT", "OCEANIE"];

/** Type de contenu Django → chemin de sa fiche sur le site. */
const CONTENT_PATHS: Record<keyof SitemapData, string> = {
  destinations: "/destinations",
  tours: "/circuits",
  hotels: "/hotels",
  residences: "/residences",
  vehicles: "/vehicules",
  activities: "/activites",
  events: "/evenements",
  offers: "/offres",
  blog: "/blog",
  albums: "/mediatheque",
  visas: "/visa",
};

async function sitemapData(): Promise<SitemapData | null> {
  try {
    const response = await backendFetch("seo/sitemap/", { next: { revalidate: 3600, tags: ["sitemap"] } });
    return response.ok ? ((await response.json()) as SitemapData) : null;
  } catch {
    return null; // Django injoignable : au moins les pages fixes
  }
}

/** Une entrée par langue, chacune annonçant toutes ses variantes. */
function entries(path: string, lastModified?: string): MetadataRoute.Sitemap {
  const languages = {
    ...Object.fromEntries(routing.locales.map((locale) => [locale, absoluteUrl(path, locale)])),
    "x-default": absoluteUrl(path, routing.defaultLocale),
  };
  return routing.locales.map((locale) => ({
    url: absoluteUrl(path, locale),
    lastModified,
    alternates: { languages },
  }));
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const data = await sitemapData();
  const pages = [
    ...STATIC_PAGES.flatMap((path) => entries(path)),
    ...CONTINENTS.flatMap((continent) => entries(`/destinations?continent=${continent}`)),
  ];
  if (data) {
    for (const [type, basePath] of Object.entries(CONTENT_PATHS) as [keyof SitemapData, string][]) {
      for (const item of data[type]) {
        pages.push(...entries(`${basePath}/${item.slug}`, item.updated_at));
      }
    }
  }
  return pages;
}
