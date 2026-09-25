import "server-only";

import { cookies } from "next/headers";
import { getLocale } from "next-intl/server";

import { ACCESS_COOKIE } from "@/lib/auth/cookies";
import { isTokenExpired } from "@/lib/auth/jwt";

import { backendFetch } from "./backend";
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
  const response = await backendFetch(
    path,
    {
      locale,
      currency: store.get(CURRENCY_COOKIE)?.value,
      token: token && !isTokenExpired(token, 0) ? token : undefined,
      ...(options.auth || options.revalidate === false
        ? { cache: "no-store" as const }
        : { next: { revalidate: options.revalidate ?? 300, tags: options.tags } }),
    },
    toSearch(options.query),
  );
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw toApiError(response.status, body);
  return body as T;
}
