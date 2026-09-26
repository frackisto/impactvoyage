/**
 * Chemin local des médias Django (« /media/… »), quel que soit l'hôte renvoyé
 * par l'API (ex. http://backend:8000 dans Docker, injoignable par le navigateur).
 * Next.js relaie /media/* vers Django (next.config.ts) et next/image les optimise
 * comme des images locales ; en production, Nginx les sert directement.
 */
export function mediaSrc(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const { pathname } = new URL(url, "http://local");
    return pathname.startsWith("/media/") ? pathname : url;
  } catch {
    return null;
  }
}
