import "server-only";

import { NextResponse } from "next/server";

import { backendFetch, unavailableResponse } from "@/lib/api/backend";

import { setAuthCookies, type TokenPair } from "./cookies";

type AuthBody = TokenPair & { refresh: string; user: unknown };

/**
 * Relaie une connexion ou une inscription à Django : les jetons reçus sont
 * posés en cookies httpOnly et seul le profil est renvoyé au navigateur.
 */
export async function forwardAuth(path: "auth/login/" | "auth/register/", request: Request) {
  const payload: unknown = await request.json().catch(() => ({}));
  const response = await backendFetch(path, {
    method: "POST",
    json: payload,
    locale: request.headers.get("accept-language") ?? undefined,
    headers: forwardedFor(request),
    cache: "no-store",
  }).catch(() => null);
  if (!response) return unavailableResponse();
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) return NextResponse.json(body, { status: response.status });

  const { access, refresh, user } = body as AuthBody;
  const result = NextResponse.json({ user }, { status: response.status });
  setAuthCookies(result.cookies, { access, refresh });
  return result;
}

/**
 * Transmet l'IP du visiteur à Django : sans cela, toutes les requêtes du BFF
 * partageraient le même quota de débit (celui du serveur Next.js).
 */
export function forwardedFor(request: Request): HeadersInit {
  const ip = request.headers.get("x-forwarded-for") ?? request.headers.get("x-real-ip");
  return ip ? { "X-Forwarded-For": ip } : {};
}
