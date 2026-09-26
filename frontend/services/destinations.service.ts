import "server-only";

import { cache } from "react";

import { nullIfNotFound } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type { DestinationDetail, DestinationList, Paginated, Review, VisaService } from "@/types";

export const CONTINENTS = ["AFRIQUE", "EUROPE", "AMERIQUES", "ASIE", "MOYEN_ORIENT", "OCEANIE"] as const;
export type Continent = (typeof CONTINENTS)[number];

export type DestinationFilters = {
  continent?: Continent;
  country?: string;
  search?: string;
  page?: number;
};

const TAGS = ["destinations"];

/** Liste filtrée et paginée (12 par page). */
export function listDestinations({ continent, country, search, page }: DestinationFilters) {
  return apiGet<Paginated<DestinationList>>("destinations/", {
    query: { continent, country, search, page, ordering: "name" },
    tags: TAGS,
  });
}

/**
 * Toutes les destinations publiées (48 au plus), pour construire les filtres :
 * continents et pays réellement proposés.
 */
export const allDestinations = cache(async (): Promise<DestinationList[]> => {
  const page = await apiGet<Paginated<DestinationList>>("destinations/", {
    query: { page_size: 48, ordering: "name" },
    tags: TAGS,
  });
  return page.results;
});

/** Fiche d'une destination ; null si elle n'existe pas ou n'est pas publiée. */
export const getDestination = cache((slug: string) =>
  nullIfNotFound(apiGet<DestinationDetail>(`destinations/${encodeURIComponent(slug)}/`, { tags: TAGS })),
);

/** Compléments de la fiche : une erreur ici n'empêche pas d'afficher la destination. */
async function optional<T>(request: Promise<T>, fallback: T): Promise<T> {
  return request.catch(() => fallback);
}

export function destinationReviews(slug: string) {
  return optional(
    apiGet<Paginated<Review>>("reviews/", {
      query: { target_type: "destination", target_slug: slug, page_size: 6 },
      tags: ["reviews"],
    }).then((page) => page.results),
    [],
  );
}

export function visasForCountry(countryCode: string) {
  return optional(
    apiGet<Paginated<VisaService>>("visas/", {
      query: { destination_country_code: countryCode, page_size: 6 },
      tags: ["visas"],
    }).then((page) => page.results),
    [],
  );
}
