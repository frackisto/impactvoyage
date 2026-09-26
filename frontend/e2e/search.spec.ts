import { expect, test } from "@playwright/test";

/**
 * Recherche globale (Phase 16). Suppose le contenu de l'agence et la démonstration :
 *   python manage.py load_agency_content && python manage.py seed_demo
 */
test.describe("page de résultats", () => {
  test("résultats tous types, onglets par type", async ({ page }) => {
    await page.goto("/recherche?q=dubai");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Résultats pour « dubai »");
    const count = page.getByRole("heading", { name: /^\d+ résultats?$/ });
    await expect(count).toHaveText("8 résultats");

    await page.getByRole("navigation", { name: "Types de résultats" }).getByRole("link", { name: /Circuits/ }).click();
    await expect(page).toHaveURL(/\/recherche\?q=dubai&type=tour$/);
    await expect(count).toHaveText("2 résultats");
    await expect(page.getByRole("link", { name: /Dubaï, la ville de tous les records/ })).toHaveAttribute(
      "href",
      "/circuits/dubai-ville-des-records",
    );
  });

  test("fautes de frappe tolérées, puis aucune correspondance", async ({ page }) => {
    await page.goto("/recherche?q=dubay");
    await expect(page.getByRole("link", { name: /Marina View Hotel Dubaï/ })).toBeVisible();

    await page.getByRole("search").getByLabel(/Rechercher une destination/).fill("xyzabc");
    await page.getByRole("search").getByRole("button", { name: "Rechercher" }).click();
    await expect(page).toHaveURL(/\/recherche\?q=xyzabc$/);
    await expect(page.getByRole("heading", { name: "Aucun résultat pour « xyzabc »" })).toBeVisible();
  });

  test("sans requête : invitation et rubriques", async ({ page }) => {
    await page.goto("/recherche");
    await expect(page.getByRole("heading", { name: "Que recherchez-vous ?" })).toBeVisible();
    await expect(page.locator('meta[name="robots"]').first()).toHaveAttribute("content", /noindex/);
  });
});

test.describe("recherche instantanée", () => {
  test("résultats pendant la frappe, Entrée ouvre la page complète", async ({ page }) => {
    await page.goto("/destinations");
    await page.getByRole("banner").getByRole("button", { name: "Rechercher" }).click();
    const dialog = page.getByRole("dialog", { name: "Rechercher sur le site" });
    const input = dialog.getByLabel(/Rechercher une destination/);
    await expect(input).toBeFocused();
    await input.pressSequentially("grand bassam");
    await expect(dialog.getByRole("link", { name: /Villa familiale à Grand-Bassam/ })).toBeVisible();
    await expect(dialog.getByRole("link", { name: /Voir les 6 résultats/ })).toBeVisible();

    await input.press("Enter");
    await expect(page).toHaveURL(/\/recherche\?q=grand\+bassam$/);
    await expect(dialog).toBeHidden();
  });

  test("données structurées de la recherche sur l'accueil", async ({ page }) => {
    await page.goto("/");
    const blocks = await page.locator('script[type="application/ld+json"]').allTextContents();
    const site = blocks.map((text) => JSON.parse(text)).find((data) => data["@type"] === "WebSite");
    expect(site.potentialAction.target.urlTemplate).toMatch(/\/recherche\?q=\{search_term_string\}$/);
  });
});
