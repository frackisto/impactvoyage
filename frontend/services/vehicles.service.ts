import "server-only";

import { cache } from "react";

import { ApiError } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type { Availability, Paginated, VehicleDetail, VehicleList } from "@/types";

export const VEHICLE_CATEGORIES = ["ECONOMIQUE", "BERLINE", "SUV", "4X4", "MINIBUS", "LUXE", "UTILITAIRE"] as const;
export const TRANSMISSIONS = ["MANUELLE", "AUTOMATIQUE"] as const;
export const VEHICLE_SORTS = ["base_price", "-base_price", "-seats", "-year"] as const;

/** Filtres « Location de véhicules » (CdC § 12), noms identiques à l'API. */
export type VehicleFilters = {
  category?: string;
  transmission?: string;
  min_seats?: number;
  max_price?: number;
  available_from?: string;
  available_to?: string;
  ordering?: string;
  page?: number;
};

const TAGS = ["vehicles"];

export function listVehicles(filters: VehicleFilters) {
  return apiGet<Paginated<VehicleList>>("vehicles/", {
    query: { ...filters, ordering: filters.ordering ?? VEHICLE_SORTS[0] },
    tags: TAGS,
  });
}

/** Catégories et boîtes réellement proposées, nombre de places maximal (48 véhicules au plus). */
export const vehicleFacets = cache(async () => {
  const page = await apiGet<Paginated<VehicleList>>("vehicles/", { query: { page_size: 48 }, tags: TAGS });
  const vehicles = page.results;
  return {
    count: page.count,
    categories: VEHICLE_CATEGORIES.filter((c) => vehicles.some((v) => v.category === c)),
    transmissions: TRANSMISSIONS.filter((t) => vehicles.some((v) => v.transmission === t)),
    maxSeats: Math.max(0, ...vehicles.map((v) => v.seats)),
  };
});

export const getVehicle = cache(async (slug: string): Promise<VehicleDetail | null> => {
  try {
    return await apiGet<VehicleDetail>(`vehicles/${encodeURIComponent(slug)}/`, { tags: TAGS });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
});

/** Disponibilité sur [start, end) et périodes réservées à partir de start ; null en cas d'échec. */
export function vehicleAvailability(slug: string, start: string, end: string) {
  return apiGet<Availability>(`vehicles/${encodeURIComponent(slug)}/availability/`, {
    query: { start, end },
    revalidate: false,
  }).catch(() => null);
}

/** Autres véhicules, de la même catégorie d'abord (3 au plus). */
export async function relatedVehicles(vehicle: VehicleDetail) {
  const page = await apiGet<Paginated<VehicleList>>("vehicles/", { query: { page_size: 12 }, tags: TAGS }).catch(() => null);
  const others = (page?.results ?? []).filter((v) => v.slug !== vehicle.slug);
  return [...others.filter((v) => v.category === vehicle.category), ...others.filter((v) => v.category !== vehicle.category)].slice(
    0,
    3,
  );
}
