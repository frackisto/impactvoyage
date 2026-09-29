import { expect, test } from "@playwright/test";

/**
 * Circuits (Phase 12). Suppose les données de démonstration chargées côté Django :
 *   python manage.py seed_demo
 */
test.describe("listes de circuits", () => {
  test("portée, filtres et tri dans l'URL", async ({ page }) => {
    await page.goto("/circuits/nationaux");
    const results = page.getByRole("heading", { name: /^\d+ circuits?$|^Aucun circuit$/ });
    await expect(results).toHaveText("3 circuits");

    await page.getByRole("navigation", { name: "Type de circuits" }).getByRole("link", { name: "Internationaux" }).click();
    await expect(page).toHaveURL(/\/circuits\/internationaux$/);
    await expect(results).toHaveText("3 circuits");

    const filters = page.getByRole("search", { name: "Filtrer les circuits" });
    if (!(await filters.isVisible())) await page.getByRole("button", { name: /Filtres/ }).click();
    await filters.getByLabel("Destination", { exact: true }).selectOption("dubai");
    await expect(page).toHaveURL(/\/circuits\/internationaux\?destination=dubai$/);
    await expect(results).toHaveText("2 circuits");

    await page.getByLabel("Trier par").selectOption("-base_price");
    await expect(page).toHaveURL(/destination=dubai&ordering=-base_price$/);
    await expect(page.getByRole("article").first()).toContainText("Lune de miel à Dubaï");
  });

  test("aucun circuit ne correspond : message et sorties", async ({ page }) => {
    await page.goto("/circuits/nationaux?max_price=1000");
    await expect(page.getByRole("heading", { name: "Aucun circuit ne correspond" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Circuit sur mesure" })).toHaveAttribute("href", "/devis?service=CIRCUIT");
  });

  test("le moteur de recherche de l'accueil mène aux résultats filtrés", async ({ page }) => {
    await page.goto("/");
    const panel = page.getByRole("tabpanel");
    await panel.getByLabel("Circuit", { exact: true }).selectOption("INTERNATIONAL");
    await panel.getByLabel("Destination", { exact: true }).selectOption("dubai");
    await panel.getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(/\/circuits\/internationaux\?destination=dubai$/);
    await expect(page.getByRole("heading", { name: "2 circuits" })).toBeVisible();
  });
});

test.describe("fiche circuit", () => {
  test("programme, départs et données structurées", async ({ page }) => {
    await page.goto("/circuits/dubai-ville-des-records");
    await expect(page.getByRole("heading", { level: 1, name: "Dubaï, la ville de tous les records" })).toBeVisible();
    const program = page.getByRole("heading", { name: "Programme jour par jour" }).locator("xpath=..").getByRole("listitem");
    await expect(program).toHaveCount(6);

    const booking = page.getByRole("complementary", { name: "Réserver ce circuit" });
    const choices = booking.getByRole("link", { name: /Réserver le départ du/ });
    await expect(choices).toHaveCount(3);
    await expect(choices.first()).toHaveAttribute("href", /\/reservation\?tour=dubai-ville-des-records&departure=\d+$/);
    await expect(booking.getByRole("link", { name: "Demander un devis" })).toHaveAttribute(
      "href",
      "/devis?tour=dubai-ville-des-records",
    );

    const jsonLd = JSON.parse((await page.locator('script[type="application/ld+json"]').textContent()) ?? "{}");
    const trip = jsonLd["@graph"][0];
    expect(trip["@type"]).toBe("TouristTrip");
    expect(trip.itinerary.numberOfItems).toBe(6);
    expect(trip.offers).toHaveLength(3);
  });

  test("places restantes et circuit sur mesure", async ({ page }) => {
    await page.goto("/circuits/abidjan-culture-et-saveurs");
    await expect(page.getByText("Plus que 3 places !")).toBeVisible();
    await page.goto("/circuits/lune-de-miel-a-dubai");
    await expect(page.getByText("Aucune date programmée", { exact: false })).toBeVisible();
  });

  test("mobile : barre de réservation vers les dates", async ({ page, isMobile }) => {
    test.skip(!isMobile, "réservé au mobile");
    await page.goto("/circuits/dubai-ville-des-records");
    await page.getByRole("link", { name: "Voir les dates" }).click();
    await expect(page).toHaveURL(/#reserver$/);
    await expect(page.getByRole("heading", { name: "Réserver ce circuit" })).toBeInViewport();
  });
});
