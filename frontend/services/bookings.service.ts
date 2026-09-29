import "server-only";

import { ApiError } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import { dateParam, intParam, param, type SearchParams } from "@/lib/search-params";
import { addDays, nights, parseStay } from "@/lib/stay";
import type { Booking, Money, Schemas } from "@/types";

import { activityAvailability, getActivity } from "./activities.service";
import { getHotel, getResidence, hotelAvailability, residenceAvailability } from "./accommodations.service";
import { getTour } from "./tours.service";
import { getVehicle, vehicleAvailability } from "./vehicles.service";

export type BookingKind = Schemas["BookingKindEnum"];

/**
 * Prestation à réserver, reconstituée côté serveur à partir du lien de la fiche.
 * Le prix est indicatif : Django le recalcule à l'envoi (aucun prix n'est transmis).
 */
export type BookingDraft = {
  kind: BookingKind;
  objectId: number;
  title: string;
  /** Chambre (hôtel). */
  detail?: string;
  href: string;
  image?: string | null;
  /** Dates envoyées à l'API (fin exclue pour les séjours et locations) ; absentes pour un départ de circuit. */
  start?: string;
  end?: string;
  /** Dates affichées (retour du circuit, dernier jour de location...). */
  displayStart?: string;
  displayEnd?: string;
  /** Quantité réservée : voyageurs, chambres ou participants ; null = toujours 1 (résidence, véhicule). */
  quantityKind: "travelers" | "rooms" | "participants" | null;
  quantity: number;
  maxQuantity: number;
  unitPrice: Money | null;
  /** Nuits ou jours facturés par unité (1 pour un circuit ou une activité). */
  periods: number;
  periodUnit: "night" | "day" | null;
  /** Lieux de prise en charge et de restitution (location de véhicule). */
  withLocations: boolean;
  /** false : l'offre n'est plus disponible aux dates choisies. */
  available: boolean;
  /** Dates ou départ à choisir sur la fiche avant de réserver. */
  needsDates: boolean;
};

const slug = (params: SearchParams, key: string) => {
  const value = param(params, key);
  return value && /^[\w-]{1,100}$/.test(value) ? value : undefined;
};

/** Prix le plus bas entre le tarif et la promotion en cours (même règle que le backend). */
function best(price: Money | null | undefined, promo: Money | null | undefined): Money | null {
  if (!price) return promo ?? null;
  if (!promo) return price;
  return Number(promo.amount) < Number(price.amount) ? promo : price;
}

/**
 * Demande de réservation préparée depuis la fiche d'origine (CdC § 12, § 13) :
 * départ de circuit, chambre d'hôtel, résidence, véhicule ou activité, avec les
 * dates et quantités du lien. null si le lien ne désigne aucune offre réservable.
 */
export async function bookingDraft(params: SearchParams): Promise<BookingDraft | null> {
  const stay = parseStay(params);
  const period = stay.start && stay.end ? { start: stay.start, end: stay.end } : undefined;

  const tourSlug = slug(params, "tour");
  if (tourSlug) {
    const tour = await getTour(tourSlug).catch(() => null);
    if (!tour) return null;
    const departure = tour.departures.find((d) => String(d.id) === param(params, "departure"));
    const seats = departure?.seats_left ?? 0;
    const travelers = intParam(params, "travelers", 1, 50) ?? 1;
    return {
      kind: "tour_departure",
      objectId: departure?.id ?? 0,
      title: tour.title,
      href: `/circuits/${tour.slug}`,
      image: tour.cover_image,
      displayStart: departure?.start_date,
      displayEnd: departure?.end_date,
      quantityKind: "travelers",
      quantity: Math.min(travelers, Math.max(seats, 1)),
      maxQuantity: Math.max(Math.min(seats, 50), 1),
      unitPrice: best(departure?.price ?? tour.price, tour.promo_price),
      periods: 1,
      periodUnit: null,
      withLocations: false,
      available: !!departure && seats > 0,
      needsDates: !departure,
    };
  }

  const hotelSlug = slug(params, "hotel");
  if (hotelSlug) {
    const hotel = await getHotel(hotelSlug).catch(() => null);
    const room = hotel?.rooms.find((r) => String(r.id) === param(params, "room"));
    if (!hotel || !room) return null;
    const availability = period ? await hotelAvailability(hotel.slug, { ...stay, rooms: 1 }) : null;
    const unitsLeft = availability?.find((row) => row.room === room.id)?.units_left ?? 0;
    return {
      kind: "room",
      objectId: room.id,
      title: hotel.name,
      detail: room.name,
      href: `/hotels/${hotel.slug}`,
      image: hotel.cover_image,
      ...period,
      displayStart: period?.start,
      displayEnd: period?.end,
      quantityKind: "rooms",
      quantity: Math.min(stay.rooms ?? 1, Math.max(unitsLeft, 1)),
      maxQuantity: Math.max(Math.min(unitsLeft, 10), 1),
      unitPrice: room.price_per_night,
      periods: nights(period?.start, period?.end),
      periodUnit: "night",
      withLocations: false,
      available: unitsLeft > 0,
      needsDates: !period,
    };
  }

  const residenceSlug = slug(params, "residence");
  if (residenceSlug) {
    const residence = await getResidence(residenceSlug).catch(() => null);
    if (!residence) return null;
    const availability = period ? await residenceAvailability(residence.slug, period) : null;
    return {
      kind: "residence",
      objectId: residence.id,
      title: residence.name,
      href: `/residences/${residence.slug}`,
      image: residence.cover_image,
      ...period,
      displayStart: period?.start,
      displayEnd: period?.end,
      quantityKind: null,
      quantity: 1,
      maxQuantity: 1,
      unitPrice: best(residence.price_per_night, residence.promo_price),
      periods: nights(period?.start, period?.end),
      periodUnit: "night",
      withLocations: false,
      available: !!availability?.available,
      needsDates: !period,
    };
  }

  const vehicleSlug = slug(params, "vehicle");
  if (vehicleSlug) {
    const vehicle = await getVehicle(vehicleSlug).catch(() => null);
    if (!vehicle) return null;
    const availability = period ? await vehicleAvailability(vehicle.slug, period.start, period.end) : null;
    return {
      kind: "vehicle",
      objectId: vehicle.id,
      title: `${vehicle.brand} ${vehicle.model}`,
      href: `/vehicules/${vehicle.slug}`,
      image: vehicle.cover_image,
      ...period,
      displayStart: period?.start,
      displayEnd: period?.end,
      quantityKind: null,
      quantity: 1,
      maxQuantity: 1,
      unitPrice: best(vehicle.price_per_day, vehicle.promo_price),
      periods: nights(period?.start, period?.end),
      periodUnit: "day",
      withLocations: true,
      available: !!availability?.available,
      needsDates: !period,
    };
  }

  const activitySlug = slug(params, "activity");
  if (activitySlug) {
    const activity = await getActivity(activitySlug).catch(() => null);
    if (!activity) return null;
    const date = dateParam(params, "date");
    const participants = intParam(params, "participants", 1, 50) ?? 1;
    const availability = date ? await activityAvailability(activity.slug, date, 1) : null;
    const placesLeft = availability ? (availability.places_left ?? 50) : 0;
    return {
      kind: "activity",
      objectId: activity.id,
      title: activity.title,
      href: `/activites/${activity.slug}`,
      image: activity.cover_image,
      start: date,
      end: date ? addDays(date, 1) : undefined,
      displayStart: date,
      quantityKind: "participants",
      quantity: Math.min(participants, Math.max(placesLeft, 1)),
      maxQuantity: Math.max(Math.min(placesLeft, activity.max_participants ?? 50, 50), 1),
      unitPrice: best(activity.price, activity.promo_price),
      periods: 1,
      periodUnit: null,
      withLocations: false,
      available: placesLeft > 0,
      needsDates: !date,
    };
  }

  return null;
}

/** Réservation consultée par le client avec le jeton reçu par email ; null si le lien est invalide. */
export async function getClientBooking(reference: string, token: string) {
  try {
    return await apiGet<Booking>(`bookings/${encodeURIComponent(reference)}/`, {
      query: { token },
      revalidate: false,
    });
  } catch (error) {
    if (error instanceof ApiError && [400, 404].includes(error.status)) return null;
    throw error;
  }
}
