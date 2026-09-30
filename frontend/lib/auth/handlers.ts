import "server-only";

import { NextResponse } from "next/server";

import { backendFetch, clientIp, unavailableResponse } from "@/lib/api/backend";
import { forbiddenOriginResponse, isSameOriginRequest } from "@/lib/security";

import { setAuthCookies, type TokenPair } from "./cookies";

type AuthBody = TokenPair & { refresh: string; user: unknown };

/**
 * Relaie une connexion ou une inscription à Django : les jetons reçus sont
 * posés en cookies httpOnly et seul le profil est renvoyé au navigateur.
 */
export async function forwardAuth(path: "auth/login/" | "auth/register/", request: Request) {
  if (!isSameOriginRequest(request)) return forbiddenOriginResponse();
  const payload: unknown = await request.json().catch(() => ({}));
  const response = await backendFetch(path, {
    method: "POST",
    json: payload,
    locale: request.headers.get("accept-language") ?? undefined,
    // Limite de débit « connexion » appliquée à l'adresse du visiteur, pas au serveur.
    clientIp: clientIp(request.headers),
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
