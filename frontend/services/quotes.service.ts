import "server-only";

import { ApiError } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import { dateParam, intParam, param, type SearchParams } from "@/lib/search-params";
import { parseStay } from "@/lib/stay";
import type { QuoteClient, Schemas } from "@/types";

import { getActivity } from "./activities.service";
import { getHotel, getResidence } from "./accommodations.service";
import { getOffer } from "./agency.service";
import { getDestination } from "./destinations.service";
import { getTour } from "./tours.service";
import { getVehicle } from "./vehicles.service";

export type QuoteValues = Partial<Schemas["QuoteRequestCreateRequest"]>;
export type RequestedService = Schemas["RequestedServiceEnum"];

export const REQUESTED_SERVICES: RequestedService[] = [
  "VOL", "HEBERGEMENT", "CIRCUIT", "VISA", "ASSURANCE", "TRANSPORT", "LOCATION_VEHICULE", "ACTIVITES", "EVENEMENT", "CONSEIL",
];

/** Prestation cochée d'office pour une offre, selon son type (aucune pour un voyage ou un package). */
const OFFER_SERVICES: Partial<Record<Schemas["OfferTypeEnum"], RequestedService>> = {
  CIRCUIT: "CIRCUIT",
  HOTEL: "HEBERGEMENT",
  BILLET: "VOL",
  LOCATION: "LOCATION_VEHICULE",
};

/** Objet d'origine de la demande (fiche d'où vient le visiteur), affiché en résumé. */
export type QuoteContext = {
  kind: "offer" | "tour" | "hotel" | "residence" | "vehicle" | "activity" | "destination";
  title: string;
  href: string;
  image?: string | null;
  start?: string;
  end?: string;
  /** Chambre choisie (hôtel). */
  room?: string;
  travelers?: number;
  rooms?: number;
  participants?: number;
};

const slug = (params: SearchParams, key: string) => {
  const value = param(params, key);
  return value && /^[\w-]{1,100}$/.test(value) ? value : undefined;
};

/**
 * Préremplissage du formulaire à partir du lien de la fiche d'origine (CdC § 18) :
 * offre, circuit et départ, hôtel et chambre, résidence, véhicule, activité,
 * destination ou prestation. Un paramètre inconnu ou un contenu introuvable est ignoré.
 */
export async function quotePrefill(params: SearchParams): Promise<{ values: QuoteValues; context: QuoteContext | null }> {
  const stay = parseStay(params);
  const service = param(params, "service");
  const values: QuoteValues = {
    services_requested: REQUESTED_SERVICES.includes(service as RequestedService) ? [service as RequestedService] : [],
  };
  const withStay = (context: QuoteContext) => {
    values.date_departure = stay.start;
    values.date_return = stay.end;
    if (stay.travelers) values.adults = stay.travelers;
    return { ...context, start: stay.start, end: stay.end, travelers: stay.travelers };
  };
  const addService = (code: RequestedService) => {
    if (!values.services_requested?.includes(code)) values.services_requested = [...(values.services_requested ?? []), code];
  };

  const offerSlug = slug(params, "offer");
  if (offerSlug) {
    const offer = await getOffer(offerSlug);
    if (offer) {
      const service = OFFER_SERVICES[offer.offer_type];
      if (service) addService(service);
      values.source_offer = offer.slug;
      values.destination = offer.destination?.slug;
      if (offer.target?.type === "tour") values.source_tour = offer.target.slug;
      return {
        values,
        context: { kind: "offer", title: offer.title, href: `/offres/${offer.slug}`, image: offer.cover_image },
      };
    }
  }

  const tourSlug = slug(params, "tour");
  if (tourSlug) {
    const tour = await getTour(tourSlug).catch(() => null);
    if (tour) {
      addService("CIRCUIT");
      values.source_tour = tour.slug;
      values.destination = tour.destination.slug;
      const departure = tour.departures.find((d) => String(d.id) === param(params, "departure"));
      values.date_departure = departure?.start_date;
      values.date_return = departure?.end_date;
      return {
        values,
        context: { kind: "tour", title: tour.title, href: `/circuits/${tour.slug}`, image: tour.cover_image, start: departure?.start_date, end: departure?.end_date },
      };
    }
  }

  const hotelSlug = slug(params, "hotel");
  if (hotelSlug) {
    const hotel = await getHotel(hotelSlug).catch(() => null);
    if (hotel) {
      addService("HEBERGEMENT");
      values.destination = hotel.destination.slug;
      const room = hotel.rooms.find((r) => String(r.id) === param(params, "room"));
      values.accommodation_pref = [hotel.name, room?.name, stay.rooms && stay.rooms > 1 ? `× ${stay.rooms}` : ""].filter(Boolean).join(" – ");
      const context = withStay({ kind: "hotel", title: hotel.name, href: `/hotels/${hotel.slug}`, image: hotel.cover_image, room: room?.name });
      return { values, context: { ...context, rooms: stay.rooms } };
    }
  }

  const residenceSlug = slug(params, "residence");
  if (residenceSlug) {
    const residence = await getResidence(residenceSlug).catch(() => null);
    if (residence) {
      addService("HEBERGEMENT");
      values.destination = residence.destination.slug;
      values.accommodation_pref = residence.name;
      return {
        values,
        context: withStay({ kind: "residence", title: residence.name, href: `/residences/${residence.slug}`, image: residence.cover_image }),
      };
    }
  }

  const vehicleSlug = slug(params, "vehicle");
  if (vehicleSlug) {
    const vehicle = await getVehicle(vehicleSlug).catch(() => null);
    if (vehicle) {
      const name = `${vehicle.brand} ${vehicle.model}`;
      addService("LOCATION_VEHICULE");
      values.transport_pref = name;
      return { values, context: withStay({ kind: "vehicle", title: name, href: `/vehicules/${vehicle.slug}`, image: vehicle.cover_image }) };
    }
  }

  const activitySlug = slug(params, "activity");
  if (activitySlug) {
    const activity = await getActivity(activitySlug).catch(() => null);
    if (activity) {
      const date = dateParam(params, "date");
      const participants = intParam(params, "participants", 1, 50);
      addService("ACTIVITES");
      values.destination = activity.destination.slug;
      values.activities = [activity.id];
      values.date_departure = date;
      if (participants) values.adults = participants;
      return {
        values,
        context: { kind: "activity", title: activity.title, href: `/activites/${activity.slug}`, image: activity.cover_image, start: date, participants },
      };
    }
  }

  const destinationSlug = slug(params, "destination");
  if (destinationSlug) {
    const destination = await getDestination(destinationSlug).catch(() => null);
    if (destination) {
      values.destination = destination.slug;
      return {
        values,
        context: { kind: "destination", title: destination.name, href: `/destinations/${destination.slug}`, image: destination.cover_image },
      };
    }
  }

  // Sans fiche d'origine (prestation seule) : date de départ et voyageurs éventuels.
  values.date_departure = stay.start ?? dateParam(params, "start");
  values.date_return = stay.end;
  if (stay.travelers) values.adults = stay.travelers;
  return { values, context: null };
}

/** Devis consulté par le client avec le jeton reçu par email ; null si le lien est invalide. */
export async function getClientQuote(reference: string, token: string) {
  try {
    return await apiGet<QuoteClient>(`quotes/${encodeURIComponent(reference)}/`, {
      query: { token },
      revalidate: false,
    });
  } catch (error) {
    if (error instanceof ApiError && [400, 404].includes(error.status)) return null;
    throw error;
  }
}
