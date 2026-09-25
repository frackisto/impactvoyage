/**
 * Lecture (sans vérification de signature) de la date d'expiration d'un JWT.
 * Sert uniquement à décider s'il faut rafraîchir le jeton : c'est Django qui
 * vérifie la signature à chaque appel.
 */
export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const part = token.split(".")[1];
  if (!part) return null;
  try {
    const base64 = part.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "="));
    const payload: unknown = JSON.parse(json);
    return payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Vrai si le jeton est absent, illisible ou expire dans moins de `skewSeconds`. */
export function isTokenExpired(token: string | undefined, skewSeconds = 30): boolean {
  if (!token) return true;
  const exp = decodeJwtPayload(token)?.exp;
  if (typeof exp !== "number") return true;
  return exp * 1000 <= Date.now() + skewSeconds * 1000;
}
