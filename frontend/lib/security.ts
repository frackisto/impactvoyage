/**
 * Règles de sécurité du serveur Next.js (Phase 23, architecture § 11) : politique de
 * sécurité du contenu (CSP) des pages, contrôle de l'origine des requêtes qui modifient
 * des données, chemins acceptés par le relais vers Django.
 */

/** Domaine de Cloudflare Turnstile (script et cadre du widget anti-robot). */
export const TURNSTILE_ORIGIN = "https://challenges.cloudflare.com";

/**
 * CSP des pages : seuls les scripts portant le nonce de la réponse (ceux de Next.js)
 * s'exécutent, et ceux qu'ils chargent eux-mêmes (« strict-dynamic » : widget Turnstile).
 * Les styles en ligne restent permis (attributs style de React et de next/image).
 */
export function contentSecurityPolicy(nonce: string, { dev = false, https = false } = {}) {
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' ${TURNSTILE_ORIGIN}${dev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src 'self' ${TURNSTILE_ORIGIN}`,
    `frame-src ${TURNSTILE_ORIGIN}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    ...(https ? ["upgrade-insecure-requests"] : []),
  ].join("; ");
}

/** Nonce aléatoire (128 bits) propre à chaque réponse. */
export function createNonce() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return btoa(String.fromCharCode(...bytes));
}

/**
 * Chemin relayé vers Django, ou null s'il est refusé. Chaque segment est déjà décodé
 * par Next.js : « %2F..%2F » donnerait « /../ » et permettrait de sortir de /api/v1
 * (backoffice, fichiers...). On n'accepte que des segments simples, réencodés.
 */
export function backendPath(segments: string[]): string | null {
  const safe = segments.every(
    (segment) => /^[\w.~@:+-]+$/.test(segment) && segment !== "." && segment !== "..",
  );
  return safe && segments.length > 0 ? `${segments.map(encodeURIComponent).join("/")}/` : null;
}

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

/**
 * Protection contre la falsification de requêtes (CSRF) : une requête qui modifie des
 * données doit venir d'une page du site. Les navigateurs envoient toujours l'en-tête
 * Origin sur un POST, et Sec-Fetch-Site ; un appel sans navigateur (curl) n'a pas de
 * cookie de session à détourner. Les cookies SameSite=Lax offrent une première barrière.
 */
export function isSameOriginRequest(request: Request): boolean {
  if (SAFE_METHODS.has(request.method)) return true;
  if (request.headers.get("sec-fetch-site") === "cross-site") return false;
  const origin = request.headers.get("origin");
  if (!origin) return true;
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
}

/** Réponse 403 au format d'erreur unique de l'API. */
export function forbiddenOriginResponse() {
  return Response.json(
    { error: { code: "forbidden_origin", message: "Requête refusée : origine non autorisée.", details: {} } },
    { status: 403 },
  );
}
