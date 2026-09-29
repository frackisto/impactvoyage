import { expect, test, type Page } from "@playwright/test";

/**
 * Hôtels et résidences (Phase 13). Suppose le contenu de l'agence et la démonstration :
 *   python manage.py load_agency_content && python manage.py seed_demo
 */
const inDays = (days: number) => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
};
const START = inDays(40);
const END = inDays(43);

async function openFilters(page: Page, name: string) {
  const filters = page.getByRole("search", { name });
  if (!(await filters.isVisible())) await page.getByRole("button", { name: /Filtres/ }).click();
  return filters;
}

test.describe("hôtels", () => {
  test("filtres : type, équipements et budget dans l'URL", async ({ page }) => {
    await page.goto("/hotels");
    const results = page.getByRole("heading", { name: /hébergements?$/ });
    await expect(results).toHaveText("5 hébergements");

    const filters = await openFilters(page, "Filtrer les hébergements");
    await filters.getByRole("checkbox", { name: "Piscine" }).check();
    await expect(page).toHaveURL(/\/hotels\?amenities=\d+$/);
    await expect(results).toHaveText("2 hébergements");

    await filters.getByLabel("Budget maximum par nuit (FCFA)").fill("60000");
    await filters.getByRole("button", { name: "Appliquer" }).click();
    await expect(results).toHaveText("1 hébergement");
    await expect(page.getByRole("link", { name: "Hôtel Lagune Plateau" })).toBeVisible();
  });

  test("le moteur de recherche de l'accueil filtre par capacité", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Hôtels" }).click();
    // Panneau nommé : pendant le changement d'onglet, l'ancien panneau est encore présent.
    const panel = page.getByRole("tabpanel", { name: "Hôtels" });
    await panel.getByLabel("Destination", { exact: true }).selectOption("abidjan");
    await panel.getByLabel("Voyageurs", { exact: true }).fill("3");
    await panel.getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(/\/hotels\?destination=abidjan&travelers=3$/);
    // Chambre double trop petite : l'hôtel reste proposé grâce à sa suite familiale.
    await expect(page.getByRole("heading", { name: "2 hébergements" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Hôtel Lagune Plateau" })).toHaveAttribute("href", /travelers=3/);
  });

  test("fiche : disponibilités des chambres et devis prérempli", async ({ page }) => {
    await page.goto(`/hotels/hotel-lagune-plateau?start=${START}&end=${END}&travelers=3`);
    await expect(page.getByRole("heading", { level: 1, name: "Hôtel Lagune Plateau" })).toBeVisible();
    await expect(page.getByText("Capacité insuffisante pour ce nombre de voyageurs")).toHaveCount(2);
    await expect(page.getByText("Disponible : 2 chambres libres")).toBeVisible();
    await expect(page.getByText(/Total pour 3 nuits/)).toHaveCount(3);
    await expect(page.getByRole("link", { name: "Réserver la chambre « Suite familiale »" })).toHaveAttribute(
      "href",
      new RegExp(`/reservation\\?hotel=hotel-lagune-plateau&room=\\d+&start=${START}&end=${END}&travelers=3$`),
    );
    await expect(page.getByRole("link", { name: "Demander un devis pour la chambre « Suite familiale »" })).toHaveAttribute(
      "href",
      new RegExp(`/devis\\?hotel=hotel-lagune-plateau&room=\\d+&start=${START}&end=${END}&travelers=3$`),
    );
    // Chambre trop petite : pas de réservation, seulement une alternative.
    await expect(page.getByRole("link", { name: /^Réserver la chambre/ })).toHaveCount(1);
    const jsonLd = JSON.parse((await page.locator('script[type="application/ld+json"]').textContent()) ?? "{}");
    expect(jsonLd["@graph"][0]["@type"]).toBe("Hotel");
    expect(jsonLd["@graph"][0].starRating.ratingValue).toBe(4);
  });

  test("fiche : choisir ses dates met la page à jour", async ({ page }) => {
    await page.goto("/hotels/marina-view-dubai");
    const form = page.getByRole("form", { name: "Vérifier les disponibilités" });
    await form.getByLabel("Arrivée").fill(START);
    await form.getByLabel("Départ").fill(END);
    await form.getByRole("button", { name: "Vérifier" }).click();
    await expect(page).toHaveURL(new RegExp(`start=${START}&end=${END}`));
    await expect(page.getByText(/^Disponible/).first()).toBeVisible();
  });
});

test.describe("résidences meublées", () => {
  test("liste et filtre de capacité", async ({ page }) => {
    await page.goto("/residences");
    const results = page.getByRole("heading", { name: /résidences?$/ });
    await expect(results).toHaveText("2 résidences");
    const filters = await openFilters(page, "Filtrer les résidences");
    await filters.getByLabel("Voyageurs").fill("5");
    await filters.getByRole("button", { name: "Appliquer" }).click();
    await expect(page).toHaveURL(/min_capacity=5$/);
    await expect(results).toHaveText("1 résidence");
  });

  test("fiche : disponibilité et total du séjour", async ({ page }) => {
    await page.goto("/residences/studio-meuble-yopougon-maroc");
    const form = page.getByRole("form", { name: "Vérifier les disponibilités" });
    await form.getByLabel("Arrivée").fill(START);
    await form.getByLabel("Départ").fill(END);
    await form.getByRole("button", { name: "Vérifier" }).click();
    const status = page.getByRole("status").filter({ hasText: "Disponible du" });
    await expect(status).toContainText("Total pour 3 nuits");
    await expect(status.getByRole("link", { name: "Réserver" })).toHaveAttribute(
      "href",
      `/reservation?residence=studio-meuble-yopougon-maroc&start=${START}&end=${END}`,
    );
    await expect(status.getByRole("link", { name: "Demander un devis" })).toHaveAttribute(
      "href",
      `/devis?residence=studio-meuble-yopougon-maroc&start=${START}&end=${END}`,
    );
  });
});
