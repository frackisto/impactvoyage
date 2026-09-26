import "server-only";

import { cache } from "react";

import { nullIfNotFound } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type { ActivityAvailability, ActivityDetail, ActivityList, Paginated } from "@/types";

/* ---------- Activités (CdC § 7) ---------- */

export const ACTIVITY_SORTS = ["base_price", "-base_price", "duration_hours", "title"] as const;

/** Filtres « Activités », noms identiques à l'API et au moteur de recherche de l'accueil. */
export type ActivityFilters = {
  destination?: string;
  category?: string;
  date?: string;
  participants?: number;
  max_hours?: number;
  max_price?: number;
  ordering?: string;
  page?: number;
};

const ACTIVITY_TAGS = ["activities"];

export function listActivities(filters: ActivityFilters) {
  return apiGet<Paginated<ActivityList>>("activities/", {
    query: { ...filters, ordering: filters.ordering ?? ACTIVITY_SORTS[0] },
    // Avec une date, les places restantes changent à chaque inscription : pas de cache.
    ...(filters.date ? { revalidate: false as const } : { tags: ACTIVITY_TAGS }),
  });
}

/** Destinations et catégories réellement proposées (48 activités au plus). */
export const activityFacets = cache(async () => {
  const page = await apiGet<Paginated<ActivityList>>("activities/", { query: { page_size: 48 }, tags: ACTIVITY_TAGS });
  const byName = (a: { name: string }, b: { name: string }) => a.name.localeCompare(b.name);
  const destinations = [...new Map(page.results.map((a) => [a.destination.slug, a.destination])).values()].sort(byName);
  const categories = [
    ...new Map(page.results.flatMap((a) => (a.category ? [[a.category.slug, a.category] as const] : []))).values(),
  ].sort(byName);
  return { count: page.count, destinations, categories };
});

export const getActivity = cache((slug: string) =>
  nullIfNotFound(apiGet<ActivityDetail>(`activities/${encodeURIComponent(slug)}/`, { tags: ACTIVITY_TAGS })),
);

/** Places restantes à une date ; null en cas d'échec. */
export function activityAvailability(slug: string, date: string, participants = 1) {
  return apiGet<ActivityAvailability>(`activities/${encodeURIComponent(slug)}/availability/`, {
    query: { date, participants },
    revalidate: false,
  }).catch(() => null);
}

/** Autres activités de la même destination, puis les autres (3 au plus). */
export async function relatedActivities(activity: ActivityDetail) {
  const page = await apiGet<Paginated<ActivityList>>("activities/", { query: { page_size: 12 }, tags: ACTIVITY_TAGS }).catch(
    () => null,
  );
  const others = (page?.results ?? []).filter((a) => a.slug !== activity.slug);
  const same = others.filter((a) => a.destination.slug === activity.destination.slug);
  return [...same, ...others.filter((a) => a.destination.slug !== activity.destination.slug)].slice(0, 3);
}
