import type { SearchResult } from "@/types";

export type SearchType = SearchResult["type"];

/** Types de la recherche globale, dans l'ordre d'affichage des onglets. */
export const SEARCH_TYPES: SearchType[] = ["destination", "tour", "hotel", "residence", "vehicle", "activity", "event"];

const PATHS: Record<SearchType, string> = {
  destination: "/destinations",
  tour: "/circuits",
  hotel: "/hotels",
  residence: "/residences",
  vehicle: "/vehicules",
  activity: "/activites",
  event: "/evenements",
};

/** Page d'un résultat de recherche (« tour » → /circuits/{slug}). */
export function resultHref(result: Pick<SearchResult, "type" | "slug">): string {
  return `${PATHS[result.type]}/${result.slug}`;
}

/** Lien vers la page de résultats. */
export function searchHref(query: string, type?: SearchType): string {
  const params = new URLSearchParams({ q: query.trim() });
  if (type) params.set("type", type);
  return `/recherche?${params}`;
}
