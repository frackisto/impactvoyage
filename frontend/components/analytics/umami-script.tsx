import { headers } from "next/headers";
import Script from "next/script";

import { SITE_URL } from "@/lib/seo";

/**
 * Mesure d'audience (architecture § 13) : Umami auto-hébergé, sans cookie. Nginx sert
 * son script et reçoit ses mesures sous /stats/ (Phase 24) : aucun domaine tiers.
 * UMAMI_WEBSITE_ID est lu au démarrage du serveur (pas au build) ; vide, rien n'est chargé.
 * Seul le domaine du site est mesuré (pas la recette ni un poste de développement), et
 * la préférence « Do Not Track » du navigateur est respectée.
 */
export async function UmamiScript() {
  const websiteId = process.env.UMAMI_WEBSITE_ID;
  if (!websiteId) return null;
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  return (
    <Script
      src="/stats/script.js"
      strategy="afterInteractive"
      nonce={nonce}
      data-website-id={websiteId}
      data-domains={new URL(SITE_URL).hostname}
      data-do-not-track="true"
    />
  );
}
