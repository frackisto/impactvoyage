import { expect, test } from "@playwright/test";

/**
 * Activités et événements (Phase 15). Suppose la démonstration chargée côté Django :
 *   python manage.py seed_demo
 * La visite de Grand-Bassam a 18 inscrits sur 20 à J+10.
 */
const inDays = (days: number) => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
};
const DAY = inDays(10);

test.describe("activités", () => {
  test("liste : date et participants filtrent sur les places restantes", async ({ page }) => {
    await page.goto("/activites");
    const results = page.getByRole("heading", { name: /^\d+ activités?$/ });
    await expect(results).toHaveText("6 activités");

    await page.goto(`/activites?date=${DAY}`);
    await expect(results).toHaveText("6 activités");
    const visit = page.getByRole("article").filter({ has: page.getByRole("link", { name: "Visite guidée de Grand-Bassam historique" }) });
    await expect(visit).toContainText("2 places restantes");

    await page.goto(`/activites?date=${DAY}&participants=3`);
    await expect(results).toHaveText("5 activités");
    await expect(page.getByRole("link", { name: "Visite guidée de Grand-Bassam historique" })).toHaveCount(0);
  });

  test("le moteur de recherche de l'accueil mène aux activités de la destination", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Activités" }).click();
    const panel = page.getByRole("tabpanel");
    await panel.getByLabel("Destination", { exact: true }).selectOption("dubai");
    await panel.getByLabel("Date", { exact: true }).fill(DAY);
    await panel.getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(new RegExp(`/activites\\?destination=dubai&date=${DAY}$`));
    await expect(page.getByRole("heading", { name: "3 activités" })).toBeVisible();
  });

  test("fiche : places insuffisantes puis réservation possible avec total", async ({ page }) => {
    await page.goto(`/activites/visite-guidee-grand-bassam?date=${DAY}&participants=3`);
    await expect(page.getByRole("status")).toContainText("Plus que 2 places");

    const form = page.getByRole("form", { name: "Vérifier les places disponibles" });
    await form.getByLabel("Participants").fill("2");
    await form.getByRole("button", { name: "Vérifier" }).click();
    const status = page.getByRole("status");
    await expect(status).toContainText("2 places restantes");
    await expect(status).toContainText("Total pour 2 participants");
    await expect(status.getByRole("link", { name: "Demander la réservation" })).toHaveAttribute(
      "href",
      `/devis?activity=visite-guidee-grand-bassam&date=${DAY}&participants=2`,
    );
  });

  test("les activités incluses apparaissent sur la fiche du circuit", async ({ page }) => {
    await page.goto("/circuits/dubai-ville-des-records");
    const section = page.getByRole("region", { name: "Activités incluses" });
    await expect(section.getByRole("article")).toHaveCount(3);
    await expect(section.getByRole("link", { name: "Safari dans le désert en 4x4" })).toHaveAttribute(
      "href",
      "/activites/safari-desert-dubai",
    );
  });
});

test.describe("événementiel", () => {
  test("liste filtrée par année", async ({ page }) => {
    await page.goto("/evenements");
    const results = page.getByRole("heading", { name: /^\d+ événements?$/ });
    await expect(results).toHaveText("3 événements");
    const filters = page.getByRole("search", { name: "Filtrer les événements" });
    if (!(await filters.isVisible())) await page.getByRole("button", { name: /Filtres/ }).click();
    await filters.getByLabel("Année").selectOption("2025");
    await expect(page).toHaveURL(/\/evenements\?year=2025$/);
    await expect(results).toHaveText("2 événements");
  });

  test("fiche : période, galerie et données structurées", async ({ page }) => {
    await page.goto("/evenements/voyage-de-groupe-dubai-2026");
    await expect(page.getByRole("heading", { level: 1, name: "Voyage de groupe à Dubaï" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "En bref" })).toContainText("14–20 mars 2026");
    await expect(page.getByRole("button", { name: /Agrandir la photo 1 sur 2/ })).toBeVisible();
    const jsonLd = JSON.parse((await page.locator('script[type="application/ld+json"]').textContent()) ?? "{}");
    expect(jsonLd["@graph"][0]).toMatchObject({ "@type": "Event", startDate: "2026-03-14", endDate: "2026-03-20" });
  });
});
