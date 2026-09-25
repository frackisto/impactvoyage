import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { backendFetch, refreshTokens, unavailableResponse } from "@/lib/api/backend";
import { CURRENCY_COOKIE } from "@/lib/api/server";
import {
  ACCESS_COOKIE,
  clearAuthCookies,
  REFRESH_COOKIE,
  setAuthCookies,
  type TokenPair,
} from "@/lib/auth/cookies";
import { forwardedFor } from "@/lib/auth/handlers";
import { isTokenExpired } from "@/lib/auth/jwt";

/**
 * BFF : relaie les appels des Client Components vers l'API Django en ajoutant
 * le jeton de l'utilisateur (lu dans le cookie httpOnly). Le jeton expiré est
 * rafraîchi, et la requête rejouée une fois si Django répond 401.
 */
async function relay(request: NextRequest, context: RouteContext<"/api/backend/[...path]">) {
  const { path } = await context.params;
  if (path.some((segment) => segment === ".." || segment === ".")) {
    return NextResponse.json(
      { error: { code: "not_found", message: "Non trouvé.", details: {} } },
      { status: 404 },
    );
  }

  const store = await cookies();
  let access = store.get(ACCESS_COOKIE)?.value;
  const refresh = store.get(REFRESH_COOKIE)?.value;
  let renewed: TokenPair | null = null;
  if (refresh && isTokenExpired(access)) {
    renewed = await refreshTokens(refresh);
    access = renewed?.access;
  }

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const body = hasBody ? await request.arrayBuffer() : null;
  const contentType = request.headers.get("content-type");
  const send = (token?: string) =>
    backendFetch(
      `${path.join("/")}/`,
      {
        method: request.method,
        body,
        token,
        locale: request.headers.get("accept-language") ?? undefined,
        currency: store.get(CURRENCY_COOKIE)?.value,
        headers: { ...(contentType ? { "Content-Type": contentType } : {}), ...forwardedFor(request) },
        cache: "no-store",
      },
      request.nextUrl.search,
    );

  let upstream = await send(access).catch(() => null);
  if (upstream?.status === 401 && refresh && !renewed) {
    renewed = await refreshTokens(refresh);
    if (renewed) upstream = await send(renewed.access).catch(() => null);
  }
  if (!upstream) return unavailableResponse();

  const response = new NextResponse(upstream.body, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
  if (renewed) setAuthCookies(response.cookies, renewed);
  else if (refresh && upstream.status === 401) clearAuthCookies(response.cookies);
  return response;
}

export {
  relay as DELETE,
  relay as GET,
  relay as PATCH,
  relay as POST,
  relay as PUT,
};
