"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "@/lib/api/client";
import type { SearchResponse } from "@/types";

/** Nombre de caractères avant de lancer la recherche instantanée. */
export const MIN_QUERY_LENGTH = 2;

/** Valeur stabilisée après `delay` ms sans changement (évite une requête par touche). */
function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/** Recherche instantanée (6 meilleurs résultats), via le BFF. */
export function useGlobalSearch(query: string) {
  const term = useDebounced(query.trim(), 250);
  return useQuery({
    queryKey: ["global-search", term],
    queryFn: async ({ signal }) =>
      (await api.get<SearchResponse>("search", { params: { q: term, limit: 6 }, signal })).data,
    enabled: term.length >= MIN_QUERY_LENGTH,
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}
