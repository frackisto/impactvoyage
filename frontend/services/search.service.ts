import "server-only";

import { apiGet } from "@/lib/api/server";
import type { SearchType } from "@/lib/search";
import type { SearchResponse } from "@/types";

/** Recherche globale (48 résultats au plus), éventuellement limitée à un type. */
export function globalSearch(query: string, type?: SearchType) {
  return apiGet<SearchResponse>("search/", {
    query: { q: query, type, limit: 48 },
    // Requêtes libres : inutile de les garder en cache.
    revalidate: false,
  });
}
