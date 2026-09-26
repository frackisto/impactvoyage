import { expect, test } from "@playwright/test";

/**
 * Page d'accueil (Phase 10). Suppose le contenu de l'agence chargé côté Django :
 *   python manage.py load_agency_content
 */
test.describe("accueil", () => {
  test("hero, sections et photos du catalogue", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    for (const title of [
      "Tout pour organiser votre voyage",
      "Où partir avec nous ?",
      "Obtenez votre visa sans stress",
      "Votre compagnon de voyage de confiance",
      "Un projet de voyage ?",
    ]) {
      await expect(page.getByRole("heading", { name: title })).toBeVisible();
    }
    // Photos Django servies par le relais /media/* et optimisées par next/image.
    const card = page.getByRole("article").filter({ has: page.getByRole("link", { name: "Dubaï", exact: true }) });
    await card.scrollIntoViewIfNeeded();
    const photo = card.getByRole("img", { name: "Dubaï" });
    await expect(photo).toHaveAttribute("src", /url=%2Fmedia%2F/);
    await expect.poll(() => photo.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  });

  test("recherche de circuits : portée et filtres dans l'URL", async ({ page }) => {
    await page.goto("/");
    const search = page.getByRole("tabpanel");
    await search.getByLabel("Circuit", { exact: true }).selectOption("INTERNATIONAL");
    await search.getByLabel("Destination", { exact: true }).selectOption("dubai");
    await search.getByLabel("Voyageurs", { exact: true }).fill("2");
    await search.getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(/\/circuits\/internationaux\?destination=dubai&travelers=2$/);
  });

  test("onglets au clavier puis recherche d'hôtels", async ({ page }) => {
    await page.goto("/");
    const tours = page.getByRole("tab", { name: "Circuits" });
    await tours.focus();
    await page.keyboard.press("ArrowRight");
    const hotels = page.getByRole("tab", { name: "Hôtels" });
    await expect(hotels).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(hotels).toHaveAttribute("aria-selected", "true");
    const panel = page.getByRole("tabpanel");
    await panel.getByLabel("Catégorie", { exact: true }).selectOption("4");
    await panel.getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(/\/hotels\?stars=4$/);
  });

  test("visa : un pays connu ouvre sa page dédiée", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Visa" }).click();
    const panel = page.getByRole("tabpanel");
    await panel.getByLabel("Pays de destination", { exact: true }).selectOption("FR");
    await panel.getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(/\/visa\/france$/);
  });
});
