import { defineRouting } from "next-intl/routing";

/**
 * Langues initiales FR/EN (CdC § 36). Le français est la langue par défaut et
 * n'a pas de préfixe : /destinations, /en/destinations.
 * Ajouter une langue = l'ajouter ici + un fichier messages/<code>.json
 * (+ "ar" dans RTL_LOCALES pour l'arabe).
 */
export const routing = defineRouting({
  locales: ["fr", "en"],
  defaultLocale: "fr",
  localePrefix: "as-needed",
});

export type Locale = (typeof routing.locales)[number];

export const RTL_LOCALES: readonly string[] = ["ar"];

export function textDirection(locale: string): "rtl" | "ltr" {
  return RTL_LOCALES.includes(locale) ? "rtl" : "ltr";
}
