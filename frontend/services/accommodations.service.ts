import "server-only";

import { cache } from "react";

import { nullIfNotFound } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type {
  Amenity,
  Availability,
  HotelDetail,
  HotelList,
  Paginated,
  ResidenceDetail,
  ResidenceList,
  Review,
  RoomAvailability,
} from "@/types";

export const HOTEL_TYPES = ["HOTEL", "APARTMENT", "PARTNER"] as const;
export const HOTEL_SORTS = ["price_from", "-price_from", "-stars", "name"] as const;
export const RESIDENCE_SORTS = ["base_price", "-base_price", "-capacity", "name"] as const;

/** Paramètres de séjour : période (fin exclue), voyageurs, chambres. */
export type Stay = { start?: string; end?: string; travelers?: number; rooms?: number };

/** Filtres « Hôtels » (CdC § 7, § 14), noms identiques à l'API et au moteur de recherche. */
export type HotelFilters = {
  destination?: string;
  accommodation_type?: string;
  stars?: number;
  amenities?: string;
  travelers?: number;
  rooms?: number;
  available_from?: string;
  available_to?: string;
  max_price?: number;
  ordering?: string;
  page?: number;
};

export type ResidenceFilters = {
  destination?: string;
  min_capacity?: number;
  min_rooms?: number;
  amenities?: string;
  available_from?: string;
  available_to?: string;
  max_price?: number;
  ordering?: string;
  page?: number;
};

const HOTEL_TAGS = ["hotels"];
const RESIDENCE_TAGS = ["residences"];

/* ---------- Hôtels ---------- */

export function listHotels(filters: HotelFilters) {
  return apiGet<Paginated<HotelList>>("hotels/", {
    query: { ...filters, ordering: filters.ordering ?? HOTEL_SORTS[0] },
    tags: HOTEL_TAGS,
  });
}

/** Destinations, types et catégories réellement proposés (48 hébergements au plus). */
export const hotelFacets = cache(async () => {
  const page = await apiGet<Paginated<HotelList>>("hotels/", { query: { page_size: 48 }, tags: HOTEL_TAGS });
  const destinations = [...new Map(page.results.map((h) => [h.destination.slug, h.destination])).values()].sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  const types = HOTEL_TYPES.filter((type) => page.results.some((h) => h.accommodation_type === type));
  const stars = [...new Set(page.results.flatMap((h) => (h.stars ? [h.stars] : [])))].sort();
  return { count: page.count, destinations, types, stars };
});

export const amenities = cache((kind: "hotel" | "residence") =>
  apiGet<Amenity[]>("amenities/", { query: { kind }, tags: [...HOTEL_TAGS, ...RESIDENCE_TAGS] }).catch(() => [] as Amenity[]),
);

export const getHotel = cache((slug: string) =>
  nullIfNotFound(apiGet<HotelDetail>(`hotels/${encodeURIComponent(slug)}/`, { tags: HOTEL_TAGS })),
);

/** Disponibilité de chaque type de chambre ; null sans période valide ou si l'API refuse. */
export async function hotelAvailability(slug: string, stay: Stay) {
  if (!stay.start || !stay.end) return null;
  return apiGet<RoomAvailability[]>(`hotels/${encodeURIComponent(slug)}/availability/`, {
    query: { start: stay.start, end: stay.end, rooms: stay.rooms, travelers: stay.travelers },
    revalidate: false,
  }).catch(() => null);
}

export function hotelReviews(slug: string) {
  return apiGet<Paginated<Review>>("reviews/", {
    query: { target_type: "hotel", target_slug: slug, page_size: 6 },
    tags: ["reviews"],
  })
    .then((page) => page.results)
    .catch(() => [] as Review[]);
}

/** Autres hébergements de la même destination, puis les autres (3 au plus). */
export async function relatedHotels(hotel: HotelDetail) {
  const page = await apiGet<Paginated<HotelList>>("hotels/", { query: { page_size: 12 }, tags: HOTEL_TAGS }).catch(() => null);
  const others = (page?.results ?? []).filter((h) => h.slug !== hotel.slug);
  const same = others.filter((h) => h.destination.slug === hotel.destination.slug);
  return [...same, ...others.filter((h) => h.destination.slug !== hotel.destination.slug)].slice(0, 3);
}

/* ---------- Résidences meublées ---------- */

export function listResidences(filters: ResidenceFilters) {
  return apiGet<Paginated<ResidenceList>>("residences/", {
    query: { ...filters, ordering: filters.ordering ?? RESIDENCE_SORTS[0] },
    tags: RESIDENCE_TAGS,
  });
}

export const residenceFacets = cache(async () => {
  const page = await apiGet<Paginated<ResidenceList>>("residences/", { query: { page_size: 48 }, tags: RESIDENCE_TAGS });
  const destinations = [...new Map(page.results.map((r) => [r.destination.slug, r.destination])).values()].sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  return { count: page.count, destinations };
});

export const getResidence = cache((slug: string) =>
  nullIfNotFound(apiGet<ResidenceDetail>(`residences/${encodeURIComponent(slug)}/`, { tags: RESIDENCE_TAGS })),
);

export async function residenceAvailability(slug: string, stay: Stay) {
  if (!stay.start || !stay.end) return null;
  return apiGet<Availability>(`residences/${encodeURIComponent(slug)}/availability/`, {
    query: { start: stay.start, end: stay.end },
    revalidate: false,
  }).catch(() => null);
}

export async function relatedResidences(residence: ResidenceDetail) {
  const page = await apiGet<Paginated<ResidenceList>>("residences/", { query: { page_size: 6 }, tags: RESIDENCE_TAGS }).catch(
    () => null,
  );
  return (page?.results ?? []).filter((r) => r.slug !== residence.slug).slice(0, 3);
}
