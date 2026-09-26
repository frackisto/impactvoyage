/**
 * Menu principal (CdC § 5), dans l'ordre du cahier des charges. `key` renvoie
 * au libellé traduit (messages/*.json, espace « Nav »).
 *
 * Sur grand écran, l'accueil passe par le logo et les entrées « secondary »
 * sont regroupées dans « Plus » ; le menu mobile affiche tout.
 */
export type NavItem = {
  key: string;
  href: string;
  secondary?: boolean;
};

export const MAIN_NAV: NavItem[] = [
  { key: "home", href: "/" },
  { key: "destinations", href: "/destinations" },
  { key: "tours", href: "/circuits/nationaux" },
  { key: "services", href: "/services" },
  { key: "offers", href: "/offres" },
  { key: "accommodations", href: "/hotels" },
  { key: "vehicles", href: "/vehicules" },
  { key: "events", href: "/evenements" },
  { key: "media", href: "/mediatheque", secondary: true },
  { key: "about", href: "/a-propos", secondary: true },
  { key: "contact", href: "/contact", secondary: true },
];

export const LEGAL_NAV: NavItem[] = [
  { key: "legalNotice", href: "/mentions-legales" },
  { key: "privacy", href: "/confidentialite" },
  { key: "terms", href: "/conditions-generales" },
];

/** Rubriques rattachées à une entrée de menu (les résidences sous « Hébergements »). */
const RELATED_SECTIONS: Record<string, string[]> = { hotels: ["residences"] };

/** Vrai si `pathname` (sans préfixe de langue) correspond à l'entrée de menu. */
export function isActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  const section = href.split("/")[1];
  return (
    pathname === href ||
    [section, ...(RELATED_SECTIONS[section] ?? [])].some((s) => pathname === `/${s}` || pathname.startsWith(`/${s}/`))
  );
}
