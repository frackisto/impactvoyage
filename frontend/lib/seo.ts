import type { Metadata } from "next";

import { getPathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";

export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

/** Nom du site dans les partages (og:site_name) et les titres de page. */
export const SITE_NAME = "Impact Voyage";

/** Image de partage par défaut (1200 × 630), pour les pages sans photo propre. */
export const DEFAULT_SHARE_IMAGE = { url: "/brand/og-default.jpg", width: 1200, height: 630 };
const DEFAULT_SHARE_ALT: Record<string, string> = {
  fr: "Impact Voyage et Logistique — votre agence de voyage à Abidjan",
  en: "Impact Voyage et Logistique — your travel agency in Abidjan",
};

/** Code Open Graph de chaque langue du site. */
const OG_LOCALES: Record<string, string> = { fr: "fr_FR", en: "en_US" };

/** Chemin localisé d'une page (« /destinations » en fr, « /en/destinations » en en). */
export function localizedPath(href: string, locale: string): string {
  return getPathname({ href, locale });
}

/** URL absolue localisée (JSON-LD, Open Graph). */
export function absoluteUrl(href: string, locale: string): string {
  return `${SITE_URL}${localizedPath(href, locale)}`;
}

/** URL canonique et variantes hreflang (CdC § 27). */
export function alternates(href: string, locale: string): Metadata["alternates"] {
  return {
    canonical: localizedPath(href, locale),
    languages: {
      ...Object.fromEntries(routing.locales.map((l) => [l, localizedPath(href, l)])),
      "x-default": localizedPath(href, routing.defaultLocale),
    },
  };
}

export type PageSeo = {
  locale: string;
  /** Chemin non localisé de la page : « /circuits/dubai ». */
  path: string;
  title: string;
  description?: string;
  /** Photo de la page (sinon l'image de partage par défaut). */
  image?: string | null;
  imageAlt?: string;
  type?: "website" | "article";
  publishedTime?: string;
  /** Titre complet, sans le suffixe « | Impact Voyage » (accueil). */
  absoluteTitle?: boolean;
  /** Page non indexée (filtres, pagination) ; ses liens restent suivis. */
  noindex?: boolean;
};

/**
 * Métadonnées complètes d'une page publique (CdC § 27) : titre, description,
 * canonique, hreflang, Open Graph et Twitter Card. Next.js ne fusionne pas
 * l'Open Graph d'un segment à l'autre : chaque page doit fournir le sien.
 */
export function pageMetadata(seo: PageSeo): Metadata {
  const images = seo.image
    ? [{ url: seo.image, alt: seo.imageAlt ?? seo.title }]
    : [{ ...DEFAULT_SHARE_IMAGE, alt: DEFAULT_SHARE_ALT[seo.locale] ?? DEFAULT_SHARE_ALT.fr }];
  return {
    title: seo.absoluteTitle ? { absolute: seo.title } : seo.title,
    description: seo.description,
    alternates: alternates(seo.path, seo.locale),
    robots: seo.noindex ? { index: false, follow: true } : undefined,
    openGraph: {
      type: seo.type ?? "website",
      siteName: SITE_NAME,
      locale: OG_LOCALES[seo.locale] ?? seo.locale,
      alternateLocale: routing.locales.filter((l) => l !== seo.locale).map((l) => OG_LOCALES[l] ?? l),
      url: absoluteUrl(seo.path, seo.locale),
      title: seo.title,
      description: seo.description,
      images,
      ...(seo.type === "article" && seo.publishedTime ? { publishedTime: seo.publishedTime } : {}),
    },
    twitter: {
      card: "summary_large_image",
      title: seo.title,
      description: seo.description,
      images: images.map((image) => image.url),
    },
  };
}
