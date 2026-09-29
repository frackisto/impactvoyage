import { readFileSync } from "node:fs";

import { type APIRequestContext, expect, type Page, test } from "@playwright/test";

/**
 * SEO (Phase 21) : plan du site, robots.txt, balises des pages et régénération à
 * la demande. Suppose les données de démonstration chargées côté Django.
 */

function sharedSecret(): string | undefined {
  try {
    const env = readFileSync(".env.local", "utf8");
    return env.match(/^FRONTEND_SHARED_SECRET=(.+)$/m)?.[1]?.trim();
  } catch {
    return undefined;
  }
}

test.describe("plan du site et robots", () => {
  test.skip(({ isMobile }) => isMobile, "pas de rendu : un seul profil suffit");

  test("sitemap.xml : pages fixes et contenus publiés, dans les deux langues", async ({ request, baseURL }) => {
    const response = await request.get("/sitemap.xml");
    expect(response.ok()).toBeTruthy();
    const xml = await response.text();
    const site = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
    for (const path of ["/", "/en", "/circuits/nationaux", "/en/contact", "/circuits/dubai-ville-des-records",
      "/en/circuits/dubai-ville-des-records", "/visa/france", "/blog/valise-pour-dubai"]) {
      expect(xml).toContain(`<loc>${site}${path}</loc>`);
    }
    // Chaque URL annonce ses variantes de langue.
    expect(xml).toContain(`hreflang="en" href="${site}/en/hotels/hotel-lagune-plateau"`);
    expect(xml).toContain(`hreflang="x-default" href="${site}/hotels/hotel-lagune-plateau"`);
    // Pages privées et listes filtrées : jamais.
    expect(xml).not.toContain("/reservation");
    expect(xml).not.toContain("/recherche");
    expect(baseURL).toBeTruthy();
  });

  test("robots.txt : pages privées exclues, plan du site annoncé", async ({ request }) => {
    const robots = await (await request.get("/robots.txt")).text();
    expect(robots).toContain("Allow: /");
    for (const path of ["/api/", "/recherche", "/reservation", "/devis/", "/en/reservation"]) {
      expect(robots).toContain(`Disallow: ${path}`);
    }
    expect(robots).toMatch(/Sitemap: .+\/sitemap\.xml/);
  });
});

/**
 * <head> tel que le lit un robot d'aperçu (WhatsApp, Facebook, Bing… : pas de JavaScript).
 * Next.js leur envoie les métadonnées dans le <head> ; aux navigateurs et à Googlebot, qui
 * exécutent le JavaScript, il les diffuse en streaming (elles peuvent suivre le <head>).
 */
async function previewHead(page: Page, request: APIRequestContext, path: string) {
  const response = await request.get(path, { headers: { "user-agent": "WhatsApp/2.23.20.0 A" } });
  const html = await response.text();
  return page.evaluate((source) => {
    const head = new DOMParser().parseFromString(source, "text/html").head;
    const attr = (selector: string, name: string) => head.querySelector(selector)?.getAttribute(name) ?? null;
    return {
      title: head.querySelector("title")?.textContent ?? null,
      canonical: attr('link[rel="canonical"]', "href"),
      hreflangFr: attr('link[hreflang="fr"]', "href"),
      hreflangDefault: attr('link[hreflang="x-default"]', "href"),
      siteName: attr('meta[property="og:site_name"]', "content"),
      locale: attr('meta[property="og:locale"]', "content"),
      ogTitle: attr('meta[property="og:title"]', "content"),
      ogUrl: attr('meta[property="og:url"]', "content"),
      ogImage: attr('meta[property="og:image"]', "content"),
      twitterCard: attr('meta[name="twitter:card"]', "content"),
    };
  }, html);
}

test.describe("balises des pages", () => {
  test("fiche circuit : aperçu WhatsApp complet (canonique, hreflang, Open Graph, Twitter)", async ({ page, request }) => {
    const head = await previewHead(page, request, "/en/circuits/dubai-ville-des-records");
    expect(head.canonical).toMatch(/\/en\/circuits\/dubai-ville-des-records$/);
    expect(head.hreflangFr).toMatch(/[^n]\/circuits\/dubai-ville-des-records$/);
    expect(head.hreflangDefault).toMatch(/[^n]\/circuits\/dubai-ville-des-records$/);
    expect(head).toMatchObject({
      siteName: "Impact Voyage",
      locale: "en_US",
      ogTitle: "Dubai, the city of records",
      twitterCard: "summary_large_image",
    });
    expect(head.ogImage).toMatch(/\/media\//);
  });

  test("accueil : titre complet et image de partage par défaut", async ({ page, request }) => {
    const head = await previewHead(page, request, "/");
    // Racine du site, avec ou sans barre finale.
    const root = /^https?:\/\/[^/]+\/?$/;
    expect(head.title).toBe("Impact Voyage et Logistique");
    expect(head.canonical).toMatch(root);
    expect(head.ogUrl).toMatch(root);
    expect(head.ogImage).toMatch(/\/brand\/og-default\.jpg$/);
  });

  test("navigateur : les balises sont présentes dans la page", async ({ page }) => {
    await page.goto("/en/circuits/dubai-ville-des-records");
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/en\/circuits\/dubai-ville-des-records$/);
    await expect(page.locator('meta[property="og:site_name"]')).toHaveAttribute("content", "Impact Voyage");
  });

  test("liste filtrée : non indexée, liens suivis", async ({ page }) => {
    await page.goto("/hotels?stars=4");
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", "noindex, follow");
    await page.goto("/hotels");
    await expect(page.locator('meta[name="robots"]')).toHaveCount(0);
  });
});

test.describe("régénération à la demande", () => {
  test.skip(({ isMobile }) => isMobile, "route serveur : un seul profil suffit");

  test("secret obligatoire, seules les étiquettes connues sont acceptées", async ({ request }) => {
    const refused = await request.post("/api/revalidate", {
      headers: { "X-Frontend-Secret": "mauvais" }, data: { tags: ["tours"] },
    });
    expect([401, 503]).toContain(refused.status());

    const secret = sharedSecret();
    test.skip(!secret, "FRONTEND_SHARED_SECRET absent de .env.local");
    const headers = { "X-Frontend-Secret": secret! };
    const unknown = await request.post("/api/revalidate", { headers, data: { tags: ["inconnue"] } });
    expect(unknown.status()).toBe(400);
    const ok = await request.post("/api/revalidate", { headers, data: { tags: ["tours", "inconnue", "sitemap"] } });
    expect(await ok.json()).toEqual({ revalidated: ["tours", "sitemap"] });
  });
});
