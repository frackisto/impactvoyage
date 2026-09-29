import { expect, test } from "@playwright/test";

/**
 * Location de véhicules (Phase 14). Suppose la démonstration chargée côté Django :
 *   python manage.py seed_demo
 * La Suzuki Vitara de démonstration est réservée de J+5 à J+9 (fin exclue).
 */
const inDays = (days: number) => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
};

test.describe("liste des véhicules", () => {
  test("filtres de catégorie, de places et de période", async ({ page }) => {
    await page.goto("/vehicules");
    const results = page.getByRole("heading", { name: /^\d+ véhicules?$/ });
    await expect(results).toHaveText("6 véhicules");

    const filters = page.getByRole("search", { name: "Filtrer les véhicules" });
    if (!(await filters.isVisible())) await page.getByRole("button", { name: /Filtres/ }).click();
    await filters.getByLabel("Places", { exact: true }).selectOption("7");
    await expect(page).toHaveURL(/\/vehicules\?min_seats=7$/);
    await expect(results).toHaveText("3 véhicules");

    // Période qui chevauche la réservation de la Vitara : elle disparaît des résultats.
    await page.goto(`/vehicules?available_from=${inDays(6)}&available_to=${inDays(8)}`);
    await expect(results).toHaveText("5 véhicules");
    await expect(page.getByText("Véhicules libres sur toute la période choisie.")).toBeVisible();
    await expect(page.getByRole("link", { name: "Suzuki Vitara" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Suzuki Ertiga" })).toHaveAttribute(
      "href",
      `/vehicules/demo-suzuki-ertiga?start=${inDays(6)}&end=${inDays(8)}`,
    );
  });
});

test.describe("fiche véhicule", () => {
  test("période déjà réservée puis période libre avec total", async ({ page }) => {
    await page.goto(`/vehicules/demo-suzuki-vitara?start=${inDays(6)}&end=${inDays(8)}`);
    await expect(page.getByRole("heading", { level: 1, name: "Suzuki Vitara" })).toBeVisible();
    await expect(page.getByRole("status").filter({ hasText: "Déjà réservé" })).toBeVisible();

    const form = page.getByRole("form", { name: "Vérifier les disponibilités" });
    await form.getByLabel("Prise en charge").fill(inDays(20));
    await form.getByLabel("Restitution").fill(inDays(23));
    await form.getByRole("button", { name: "Vérifier" }).click();
    const status = page.getByRole("status").filter({ hasText: "Disponible du" });
    await expect(status).toContainText("Total pour 3 jours");
    await expect(status.getByRole("link", { name: "Réserver" })).toHaveAttribute(
      "href",
      `/reservation?vehicle=demo-suzuki-vitara&start=${inDays(20)}&end=${inDays(23)}`,
    );
    await expect(status.getByRole("link", { name: "Demander un devis" })).toHaveAttribute(
      "href",
      `/devis?vehicle=demo-suzuki-vitara&start=${inDays(20)}&end=${inDays(23)}`,
    );
  });

  test("calendrier des réservations et données structurées", async ({ page }) => {
    await page.goto("/vehicules/demo-suzuki-vitara");
    // Deux mois affichés ; les 4 jours réservés sont annoncés aux lecteurs d'écran.
    await expect(page.getByRole("table")).toHaveCount(2);
    await expect(page.getByRole("cell", { name: /: réservé$/ })).toHaveCount(4);
    const jsonLd = JSON.parse((await page.locator('script[type="application/ld+json"]').textContent()) ?? "{}");
    const car = jsonLd["@graph"][0];
    expect(car["@type"]).toBe("Car");
    expect(car.vehicleSeatingCapacity).toBe(5);
    expect(car.offers.priceSpecification.unitCode).toBe("DAY");
  });
});
