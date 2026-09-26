import type { Metadata } from "next";

import { getPathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";

export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

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
