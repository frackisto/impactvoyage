import { createHash, timingSafeEqual } from "node:crypto";

import { revalidateTag } from "next/cache";

/**
 * Régénération à la demande (architecture § 9) : Django appelle cette route
 * quand un contenu public change dans l'admin (backend/apps/core/revalidation.py),
 * avec le secret partagé FRONTEND_SHARED_SECRET. Les pages qui utilisent ces
 * étiquettes de cache sont recalculées à la visite suivante, sans servir
 * l'ancienne version.
 */
const CACHE_TAGS = new Set([
  "destinations", "tours", "hotels", "residences", "vehicles", "activities", "events",
  "offers", "media", "services", "visas", "transport", "blog", "categories", "reviews",
  "site-settings", "sitemap",
]);

function error(status: number, code: string, message: string) {
  return Response.json({ error: { code, message, details: {} } }, { status });
}

/** Comparaison à durée constante (les empreintes ont toujours la même longueur). */
function sameSecret(given: string, expected: string) {
  const digest = (value: string) => createHash("sha256").update(value).digest();
  return timingSafeEqual(digest(given), digest(expected));
}

export async function POST(request: Request) {
  const secret = process.env.FRONTEND_SHARED_SECRET;
  if (!secret) return error(503, "disabled", "Régénération désactivée : FRONTEND_SHARED_SECRET est vide.");
  if (!sameSecret(request.headers.get("x-frontend-secret") ?? "", secret)) {
    return error(401, "invalid_secret", "Secret invalide.");
  }

  const body: unknown = await request.json().catch(() => null);
  const requested = (body as { tags?: unknown } | null)?.tags;
  const tags = Array.isArray(requested)
    ? requested.filter((tag): tag is string => typeof tag === "string" && CACHE_TAGS.has(tag))
    : [];
  if (!tags.length) return error(400, "invalid_tags", "Aucune étiquette de cache connue.");

  for (const tag of tags) revalidateTag(tag, { expire: 0 });
  return Response.json({ revalidated: tags });
}
