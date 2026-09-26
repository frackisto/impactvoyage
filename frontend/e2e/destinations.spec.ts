import { expect, test } from "@playwright/test";

/**
 * Destinations (Phase 11). Suppose le contenu de l'agence chargé côté Django :
 *   python manage.py load_agency_content
 */
test.describe("liste des destinations", () => {
  test("filtres par continent, pays et nom dans l'URL", async ({ page }) => {
    await page.goto("/destinations");
    const results = page.getByRole("heading", { name: /\d+ destinations?$/ });
    const filters = page.getByRole("search", { name: "Filtrer les destinations" });
    await expect(results).toHaveText("6 destinations");

    await page.getByRole("navigation", { name: "Continents" }).getByRole("link", { name: /Afrique/ }).click();
    await expect(page).toHaveURL(/\/destinations\?continent=AFRIQUE$/);
    await expect(results).toHaveText("3 destinations");
    // Le choix du pays est limité au continent sélectionné.
    await expect(filters.getByLabel("Pays", { exact: true }).locator("option")).toHaveCount(2);

    await filters.getByLabel("Rechercher", { exact: true }).fill("lahou");
    await filters.getByRole("button", { name: "Filtrer" }).click();
    await expect(page).toHaveURL(/continent=AFRIQUE&search=lahou$/);
    await expect(results).toHaveText("1 destination");
    await expect(page.getByRole("link", { name: "Grand-Lahou" })).toBeVisible();

    await filters.getByRole("link", { name: "Réinitialiser" }).click();
    await expect(page).toHaveURL(/\/destinations$/);
    await filters.getByLabel("Pays", { exact: true }).selectOption("AE");
    await expect(page).toHaveURL(/\/destinations\?country=AE$/);
    await expect(results).toHaveText("1 destination");
  });

  test("aucun résultat : message et sorties", async ({ page }) => {
    await page.goto("/destinations?continent=OCEANIE");
    await expect(page.getByRole("heading", { name: "Aucune destination trouvée" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Voyage sur mesure" })).toHaveAttribute("href", "/devis");
  });
});

test.describe("fiche destination", () => {
  test("contenu, encadré pratique et données structurées", async ({ page }) => {
    await page.goto("/destinations/dubai");
    await expect(page.getByRole("heading", { level: 1, name: "Dubaï" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Découvrir Dubaï" })).toBeVisible();
    const aside = page.getByRole("complementary", { name: "Préparer votre voyage" });
    await expect(aside.getByRole("link", { name: /Visa .* nos formalités/ })).toHaveAttribute("href", "/visa/dubai");
    await expect(aside.getByRole("link", { name: "Demander un devis" })).toHaveAttribute("href", "/devis?destination=dubai");
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/destinations\/dubai$/);
    const jsonLd = JSON.parse((await page.locator('script[type="application/ld+json"]').textContent()) ?? "{}");
    expect(jsonLd["@graph"].map((item: { "@type": string }) => item["@type"])).toEqual([
      "TouristDestination",
      "BreadcrumbList",
    ]);
  });

  test("galerie : visionneuse au clavier", async ({ page }) => {
    await page.goto("/destinations/dubai");
    const thumbnail = page.getByRole("button", { name: /Agrandir la photo 1 sur 3/ });
    await thumbnail.click();
    const viewer = page.getByRole("dialog");
    await expect(viewer).toContainText("photo 1 sur 3");
    await page.keyboard.press("ArrowRight");
    await expect(viewer).toContainText("photo 2 sur 3");
    await page.keyboard.press("ArrowLeft");
    await page.keyboard.press("ArrowLeft");
    await expect(viewer).toContainText("photo 3 sur 3");
    await page.keyboard.press("Escape");
    await expect(viewer).toBeHidden();
    await expect(thumbnail).toBeFocused();
  });

  test("version anglaise et destination inconnue", async ({ page }) => {
    await page.goto("/destinations/inconnue");
    await expect(page.getByRole("heading", { name: "Page introuvable" })).toBeVisible();
    await expect(page.locator('meta[name="robots"][content="noindex"]').first()).toBeAttached();
    // Après /en, la langue est mémorisée (cookie) : on termine par la version anglaise.
    await page.goto("/en/destinations/chine");
    await expect(page.getByRole("heading", { level: 1, name: "China" })).toBeVisible();
  });
});
