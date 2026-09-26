import "server-only";

/**
 * Appels serveur → Django (Server Components, Route Handlers, proxy).
 * API_URL n'est jamais exposée au navigateur : en Docker, c'est l'adresse
 * interne du service backend.
 */
export const API_URL = (process.env.API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

/**
 * Secret partagé avec Django (FRONTEND_SHARED_SECRET) : il identifie ce serveur
 * pour la limitation de débit (voir backend/apps/core/throttling.py).
 */
const FRONTEND_SECRET = process.env.FRONTEND_SHARED_SECRET;

export type BackendRequest = {
  method?: string;
  body?: BodyInit | null;
  json?: unknown;
  token?: string;
  locale?: string;
  currency?: string;
  /**
   * Adresse du visiteur, pour les requêtes qui lui sont propres (connexion,
   * formulaires, disponibilités) : Django lui applique la limite de débit.
   * Absente : lecture publique mise en cache, non limitée par Django.
   */
  clientIp?: string;
  headers?: HeadersInit;
  next?: NextFetchRequestConfig;
  cache?: RequestCache;
};

/**
 * Adresse du visiteur d'après les en-têtes de la requête entrante : X-Real-IP
 * (posé par Nginx en production), sinon la dernière entrée de X-Forwarded-For
 * (ajoutée par le dernier proxy : les entrées précédentes peuvent être falsifiées).
 */
export function clientIp(headers: Headers): string | undefined {
  const real = headers.get("x-real-ip")?.trim();
  if (real) return real;
  const forwarded = headers.get("x-forwarded-for")?.split(",").map((ip) => ip.trim()).filter(Boolean);
  return forwarded?.at(-1);
}

export function backendUrl(path: string, search = ""): string {
  const clean = path.replace(/^\/+/, "");
  return `${API_URL}/${clean}${search}`;
}

export async function backendFetch(path: string, options: BackendRequest = {}, search = "") {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);
  if (options.locale) headers.set("Accept-Language", options.locale);
  if (options.currency) headers.set("X-Currency", options.currency);
  if (FRONTEND_SECRET) {
    headers.set("X-Frontend-Secret", FRONTEND_SECRET);
    if (options.clientIp) headers.set("X-Client-IP", options.clientIp);
  }
  let body = options.body;
  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }
  return fetch(backendUrl(path, search), {
    method: options.method ?? "GET",
    headers,
    body,
    next: options.next,
    cache: options.cache,
  });
}

/** Réponse 503 au format d'erreur unique, quand Django est injoignable. */
export function unavailableResponse() {
  return Response.json(
    {
      error: {
        code: "service_unavailable",
        message: "Service momentanément indisponible. Réessayez dans un instant.",
        details: {},
      },
    },
    { status: 503 },
  );
}

/** Rafraîchit la paire de jetons (rotation côté Django). null si le refresh est invalide. */
export async function refreshTokens(refresh: string, clientIp?: string) {
  const response = await backendFetch("auth/refresh/", {
    method: "POST",
    json: { refresh },
    clientIp,
    cache: "no-store",
  }).catch(() => null);
  if (!response?.ok) return null;
  return (await response.json()) as { access: string; refresh: string };
}
