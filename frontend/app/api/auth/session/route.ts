import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { backendFetch, refreshTokens, unavailableResponse } from "@/lib/api/backend";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies,
  type TokenPair,
} from "@/lib/auth/cookies";
import { isTokenExpired } from "@/lib/auth/jwt";

/**
 * Utilisateur connecté ({user: null} sinon), pour l'en-tête et l'espace client.
 * Rafraîchit le jeton d'accès s'il a expiré.
 */
export async function GET() {
  const store = await cookies();
  let access = store.get(ACCESS_COOKIE)?.value;
  const refresh = store.get(REFRESH_COOKIE)?.value;
  let renewed: TokenPair | null = null;

  if (isTokenExpired(access) && refresh) {
    renewed = await refreshTokens(refresh);
    access = renewed?.access;
  }
  if (!access || isTokenExpired(access, 0)) {
    const response = NextResponse.json({ user: null });
    if (refresh) clearAuthCookies(response.cookies);
    return response;
  }

  const me = await backendFetch("auth/me/", { token: access, cache: "no-store" }).catch(() => null);
  if (!me) return unavailableResponse();
  const response = NextResponse.json({ user: me.ok ? await me.json() : null });
  if (renewed) setAuthCookies(response.cookies, renewed);
  if (!me.ok) clearAuthCookies(response.cookies);
  return response;
}
