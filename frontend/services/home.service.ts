import "server-only";

import { apiGet } from "@/lib/api/server";
import type {
  Category,
  DestinationList,
  EventList,
  OfferList,
  Paginated,
  ResidenceList,
  Review,
  Service,
  TourList,
  VisaService,
} from "@/types";

/** Une section en erreur (API injoignable, liste vide) est masquée, le reste de la page s'affiche. */
async function safe<T>(request: Promise<T>, fallback: T): Promise<T> {
  try {
    return await request;
  } catch {
    return fallback;
  }
}

const results = <T,>(page: Promise<Paginated<T>>) => safe(page.then((p) => p.results), [] as T[]);

/** Données de la page d'accueil, chargées en parallèle et mises en cache 5 min. */
export async function getHomeData() {
  const [services, destinations, allDestinations, tours, offers, visas, residences, events, reviews, themes] =
    await Promise.all([
      safe(apiGet<Service[]>("services/", { tags: ["services"] }), []),
      results(apiGet<Paginated<DestinationList>>("destinations/", { query: { featured: true, page_size: 8 } })),
      results(apiGet<Paginated<DestinationList>>("destinations/", { query: { page_size: 48 } })),
      results(apiGet<Paginated<TourList>>("tours/", { query: { page_size: 6, ordering: "next_departure" } })),
      results(apiGet<Paginated<OfferList>>("offers/", { query: { page_size: 3 } })),
      results(apiGet<Paginated<VisaService>>("visas/", { query: { page_size: 12 } })),
      results(apiGet<Paginated<ResidenceList>>("residences/", { query: { page_size: 3 } })),
      results(apiGet<Paginated<EventList>>("events/", { query: { page_size: 3 } })),
      results(apiGet<Paginated<Review>>("reviews/", { query: { featured: true, page_size: 6 } })),
      safe(apiGet<Category[]>("categories/", { query: { kind: "TOUR_THEME" } }), []),
    ]);
  return { services, destinations, allDestinations, tours, offers, visas, residences, events, reviews, themes };
}

export type HomeData = Awaited<ReturnType<typeof getHomeData>>;
