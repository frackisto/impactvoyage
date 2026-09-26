import "server-only";

import { cache } from "react";

import { nullIfNotFound } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type { EventDetail, EventList, Paginated } from "@/types";

/* ---------- Événementiel (CdC § 15) ---------- */

export const EVENT_CATEGORIES = [
  "VOYAGE_GROUPE", "EXCURSION", "PROFESSIONNEL", "CULTUREL", "SPORTIF", "TOURISTIQUE", "PRIVE", "AUTRE",
] as const;

export type EventFilters = { category?: string; year?: number; page?: number };

const EVENT_TAGS = ["events"];

export function listEvents(filters: EventFilters) {
  return apiGet<Paginated<EventList>>("events/", { query: { ...filters, ordering: "-date" }, tags: EVENT_TAGS });
}

/** Catégories et années réellement présentes (48 événements au plus). */
export const eventFacets = cache(async () => {
  const page = await apiGet<Paginated<EventList>>("events/", { query: { page_size: 48 }, tags: EVENT_TAGS });
  return {
    count: page.count,
    categories: EVENT_CATEGORIES.filter((c) => page.results.some((e) => e.category === c)),
    years: [...new Set(page.results.map((e) => Number(e.date.slice(0, 4))))].sort((a, b) => b - a),
  };
});

export const getEvent = cache((slug: string) =>
  nullIfNotFound(apiGet<EventDetail>(`events/${encodeURIComponent(slug)}/`, { tags: EVENT_TAGS })),
);

export async function relatedEvents(event: EventDetail) {
  const page = await apiGet<Paginated<EventList>>("events/", { query: { page_size: 6, ordering: "-date" }, tags: EVENT_TAGS }).catch(
    () => null,
  );
  return (page?.results ?? []).filter((e) => e.slug !== event.slug).slice(0, 3);
}
