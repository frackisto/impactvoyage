import "server-only";

import { cookies, headers } from "next/headers";
import { getLocale } from "next-intl/server";

import { ACCESS_COOKIE } from "@/lib/auth/cookies";
import { isTokenExpired } from "@/lib/auth/jwt";

import { backendFetch, clientIp } from "./backend";
import { toApiError } from "./errors";

export const CURRENCY_COOKIE = "iv_currency";

type Query = Record<string, string | number | boolean | undefined | null>;

export type ServerGetOptions = {
  query?: Query;
  /** Durée de cache en secondes (ISR) ; false = jamais mis en cache. */
  revalidate?: number | false;
  tags?: string[];
  /** Envoie le jeton de l'utilisateur connecté (données privées, jamais mises en cache). */
  auth?: boolean;
};

function toSearch(query?: Query): string {
  if (!query) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const search = params.toString();
  return search ? `?${search}` : "";
}

/**
 * GET typé depuis un Server Component, dans la langue et la devise du visiteur :
 *   const tours = await apiGet<components["schemas"]["PaginatedTourListList"]>("tours/")
 */
export async function apiGet<T>(path: string, options: ServerGetOptions = {}): Promise<T> {
  const [locale, store] = await Promise.all([getLocale(), cookies()]);
  const token = options.auth ? store.get(ACCESS_COOKIE)?.value : undefined;
  const personal = options.auth || options.revalidate === false;
  const response = await backendFetch(
    path,
    {
      locale,
      currency: store.get(CURRENCY_COOKIE)?.value,
      token: token && !isTokenExpired(token, 0) ? token : undefined,
      // Requête propre au visiteur (non mise en cache) : Django limite son adresse à lui.
      // Pas pour les lectures en cache : l'adresse ferait partie de la clé de cache.
      clientIp: personal ? clientIp(await headers()) : undefined,
      ...(personal
        ? { cache: "no-store" as const }
        : { next: { revalidate: options.revalidate ?? 300, tags: options.tags } }),
    },
    toSearch(options.query),
  );
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw toApiError(response.status, body);
  return body as T;
}
