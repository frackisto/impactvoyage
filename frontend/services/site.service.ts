import "server-only";

import { cache } from "react";

import { apiGet } from "@/lib/api/server";
import type { SiteSettings } from "@/types";

/**
 * Coordonnées et paramètres de l'agence (éditables dans l'admin), mis en cache
 * 1 h. Si l'API est indisponible, le site reste affiché sans ces informations.
 */
export const getSiteSettings = cache(async (): Promise<Partial<SiteSettings>> => {
  try {
    return await apiGet<SiteSettings>("site-settings/", { revalidate: 3600, tags: ["site-settings"] });
  } catch {
    return {};
  }
});

export function socialLinks(settings: Partial<SiteSettings>): [string, string][] {
  const links = settings.social_links;
  if (!links || typeof links !== "object") return [];
  return Object.entries(links as Record<string, unknown>).filter(
    (entry): entry is [string, string] => typeof entry[1] === "string" && entry[1].startsWith("http"),
  );
}

/** Lien WhatsApp à partir d'un numéro saisi librement (« +225 07 00 00 00 00 »). */
export function whatsappUrl(number: string | undefined): string | null {
  const digits = (number ?? "").replace(/\D/g, "");
  return digits ? `https://wa.me/${digits}` : null;
}
