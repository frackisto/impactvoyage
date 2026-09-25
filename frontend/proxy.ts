import createMiddleware from "next-intl/middleware";
import { NextResponse, type NextRequest } from "next/server";

import { routing } from "@/i18n/routing";
import { refreshTokens } from "@/lib/api/backend";
import { ACCESS_COOKIE, clearAuthCookies, REFRESH_COOKIE, setAuthCookies } from "@/lib/auth/cookies";
import { isTokenExpired } from "@/lib/auth/jwt";

const intl = createMiddleware(routing);

/** Pages réservées aux utilisateurs connectés (CdC § 24). */
const PROTECTED_PATHS = ["/profile"];

function splitLocale(pathname: string): { locale: string; path: string } {
  const [, first, ...rest] = pathname.split("/");
  if ((routing.locales as readonly string[]).includes(first)) {
    return { locale: first, path: `/${rest.join("/")}` };
  }
  return { locale: routing.defaultLocale, path: pathname };
}

function loginUrl(request: NextRequest, locale: string) {
  const prefix = locale === routing.defaultLocale ? "" : `/${locale}`;
  const url = new URL(`${prefix}/login`, request.url);
  url.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
  return url;
}

export default async function proxy(request: NextRequest) {
  const { locale, path } = splitLocale(request.nextUrl.pathname);
  const isProtected = PROTECTED_PATHS.some((p) => path === p || path.startsWith(`${p}/`));

  if (isProtected && isTokenExpired(request.cookies.get(ACCESS_COOKIE)?.value)) {
    const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
    const renewed = refresh ? await refreshTokens(refresh) : null;
    if (!renewed) {
      const response = NextResponse.redirect(loginUrl(request, locale));
      clearAuthCookies(response.cookies);
      return response;
    }
    // Recharge la même page avec les nouveaux cookies : les Server Components
    // de la requête suivante disposent d'un jeton valide.
    const response = NextResponse.redirect(request.nextUrl);
    setAuthCookies(response.cookies, renewed);
    return response;
  }

  return intl(request);
}

export const config = {
  // Tout sauf l'API du BFF, les fichiers internes de Next.js et les fichiers statiques.
  matcher: "/((?!api|_next|_vercel|.*\\..*).*)",
};
