import { dateParam, intParam, type SearchParams } from "./search-params";

/** Séjour lu dans l'URL : arrivée, départ (exclu), voyageurs, chambres. */
export type Stay = { start?: string; end?: string; travelers?: number; rooms?: number };

const DAY = 86_400_000;

/** Nombre de nuits entre deux dates AAAA-MM-JJ (0 si la période est invalide). */
export function nights(start?: string, end?: string): number {
  if (!start || !end) return 0;
  const count = Math.round((Date.parse(end) - Date.parse(start)) / DAY);
  return Number.isFinite(count) && count > 0 ? count : 0;
}

/**
 * Séjour valide ou incomplet : une période n'est retenue que si le départ suit
 * l'arrivée, sur un an au plus (limite de l'API).
 */
export function parseStay(params: SearchParams, keys = { start: "start", end: "end" }): Stay {
  const start = dateParam(params, keys.start);
  const end = dateParam(params, keys.end);
  const count = nights(start, end);
  const period = count > 0 && count <= 366 ? { start, end } : {};
  return {
    ...period,
    travelers: intParam(params, "travelers", 1, 20),
    rooms: intParam(params, "rooms", 1, 10),
  };
}

/** Paramètres d'URL d'un séjour (clés absentes si vides). */
export function stayQuery(stay: Stay): Record<string, string | undefined> {
  return {
    start: stay.start,
    end: stay.end,
    travelers: stay.travelers ? String(stay.travelers) : undefined,
    rooms: stay.rooms && stay.rooms > 1 ? String(stay.rooms) : undefined,
  };
}

/** Date AAAA-MM-JJ décalée de `days` jours (calcul en UTC, sans effet de fuseau). */
export function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** Aujourd'hui, AAAA-MM-JJ. */
export function today(): string {
  return new Date().toISOString().slice(0, 10);
}
