import { intlLocale } from "./format";

/** Nom du pays dans la langue du visiteur à partir de son code ISO (« AE » → « Émirats arabes unis »). */
export function countryName(code: string, locale: string): string {
  try {
    return new Intl.DisplayNames([intlLocale(locale)], { type: "region" }).of(code.toUpperCase()) ?? code;
  } catch {
    return code;
  }
}

/** Drapeau emoji à partir du code ISO (« CI » → 🇨🇮). */
export function countryFlag(code: string): string {
  return code
    .toUpperCase()
    .replace(/./g, (letter) => String.fromCodePoint(127397 + letter.charCodeAt(0)));
}

/**
 * Pays de résidence proposés dans les formulaires : Afrique de l'Ouest et
 * centrale, Maghreb et principaux pays de la diaspora. Triés à l'affichage.
 */
export const RESIDENCE_COUNTRIES = [
  "CI", "BF", "BJ", "CM", "CD", "CG", "GA", "GH", "GN", "LR", "ML", "MR", "NE", "NG", "SN", "SL", "TG",
  "DZ", "MA", "TN", "ZA", "BE", "CA", "CH", "CN", "DE", "ES", "FR", "GB", "IT", "LB", "AE", "US",
];
