/**
 * Cookies d'authentification (architecture § 6.1) : jamais lisibles par le
 * JavaScript du navigateur (httpOnly), envoyés uniquement en HTTPS en production.
 */
export const ACCESS_COOKIE = "iv_access";
export const REFRESH_COOKIE = "iv_refresh";

const ACCESS_MAX_AGE = 15 * 60; // aligné sur ACCESS_TOKEN_LIFETIME (Django)
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60; // aligné sur REFRESH_TOKEN_LIFETIME

type CookieOptions = {
  httpOnly: true;
  secure: boolean;
  sameSite: "lax";
  path: string;
  maxAge: number;
};

function baseOptions(maxAge: number): CookieOptions {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge,
  };
}

export const accessCookieOptions = () => baseOptions(ACCESS_MAX_AGE);
export const refreshCookieOptions = () => baseOptions(REFRESH_MAX_AGE);

export type TokenPair = { access: string; refresh?: string };

/** Pose les jetons sur une réponse (NextResponse.cookies). */
export function setAuthCookies(
  cookies: { set: (name: string, value: string, options: CookieOptions) => unknown },
  tokens: TokenPair,
) {
  cookies.set(ACCESS_COOKIE, tokens.access, accessCookieOptions());
  if (tokens.refresh) cookies.set(REFRESH_COOKIE, tokens.refresh, refreshCookieOptions());
}

export function clearAuthCookies(cookies: { delete: (name: string) => unknown }) {
  cookies.delete(ACCESS_COOKIE);
  cookies.delete(REFRESH_COOKIE);
}
