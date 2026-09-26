import "server-only";

import { cache } from "react";

import { ApiError } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type { Paginated, Review, TourDetail, TourList } from "@/types";

export type TourScope = "NATIONAL" | "INTERNATIONAL";

/** Chemin des listes : /circuits/nationaux, /circuits/internationaux. */
export const SCOPE_PATHS: Record<TourScope, string> = {
  NATIONAL: "/circuits/nationaux",
  INTERNATIONAL: "/circuits/internationaux",
};

export const TOUR_SORTS = ["next_departure", "base_price", "-base_price", "duration_days"] as const;
export type TourSort = (typeof TOUR_SORTS)[number];

/** Filtres du moteur de recherche « Tours » (CdC § 7, § 10), noms identiques à l'API. */
export type TourFilters = {
  destination?: string;
  theme?: string;
  departure_from?: string;
  departure_to?: string;
  max_days?: number;
  travelers?: number;
  max_price?: number;
  search?: string;
  ordering?: TourSort;
  page?: number;
};

const TAGS = ["tours"];

export function listTours(scope: TourScope, filters: TourFilters) {
  return apiGet<Paginated<TourList>>("tours/", {
    query: { scope, ...filters, ordering: filters.ordering ?? "next_departure" },
    tags: TAGS,
  });
}

/**
 * Destinations et thèmes réellement proposés dans une portée (48 circuits au plus),
 * pour que les filtres ne mènent jamais à une liste vide par construction.
 */
export const tourFacets = cache(async (scope: TourScope) => {
  const page = await apiGet<Paginated<TourList>>("tours/", {
    query: { scope, page_size: 48, ordering: "title" },
    tags: TAGS,
  });
  const byName = (a: { name: string }, b: { name: string }) => a.name.localeCompare(b.name);
  const destinations = [...new Map(page.results.map((t) => [t.destination.slug, t.destination])).values()].sort(byName);
  const themes = [
    ...new Map(page.results.flatMap((t) => (t.theme ? [[t.theme.slug, t.theme] as const] : []))).values(),
  ].sort(byName);
  return { count: page.count, destinations, themes };
});

/** Fiche d'un circuit ; null s'il n'existe pas ou n'est pas publié. */
export const getTour = cache(async (slug: string): Promise<TourDetail | null> => {
  try {
    return await apiGet<TourDetail>(`tours/${encodeURIComponent(slug)}/`, { tags: TAGS });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
});

export function tourReviews(slug: string) {
  return apiGet<Paginated<Review>>("reviews/", {
    query: { target_type: "tour", target_slug: slug, page_size: 6 },
    tags: ["reviews"],
  })
    .then((page) => page.results)
    .catch(() => [] as Review[]);
}

/** Autres circuits de la même destination, puis de la même portée (3 au plus). */
export async function relatedTours(tour: TourDetail) {
  const [sameDestination, sameScope] = await Promise.all([
    apiGet<Paginated<TourList>>("tours/", { query: { destination: tour.destination.slug, page_size: 4 }, tags: TAGS }),
    apiGet<Paginated<TourList>>("tours/", { query: { scope: tour.scope, page_size: 6 }, tags: TAGS }),
  ]).catch(() => [null, null]);
  const seen = new Set([tour.slug]);
  return [...(sameDestination?.results ?? []), ...(sameScope?.results ?? [])]
    .filter((t) => !seen.has(t.slug) && seen.add(t.slug))
    .slice(0, 3);
}
