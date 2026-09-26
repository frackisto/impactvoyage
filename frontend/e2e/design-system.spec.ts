import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const PAGES = [
  "/",
  "/en",
  "/charte-graphique",
  "/destinations",
  "/destinations/dubai",
  "/circuits/nationaux",
  "/circuits/dubai-ville-des-records",
  "/hotels",
  "/hotels/hotel-lagune-plateau",
  "/residences/studio-meuble-yopougon-maroc",
  "/vehicules",
  "/vehicules/demo-suzuki-vitara",
  "/activites",
  "/activites/visite-guidee-grand-bassam",
  "/evenements",
  "/evenements/voyage-de-groupe-dubai-2026",
  "/recherche?q=dubai",
];

test.describe("design system", () => {
  for (const path of PAGES) {
    test(`accessibilité WCAG 2.2 AA : ${path}`, async ({ page }, testInfo) => {
      // axe est lent sur les pages riches (calendriers) en émulation mobile.
      test.setTimeout(60_000);
      await page.goto(path);
      // Trace visuelle seulement : Chrome refuse parfois une capture pleine page en
      // émulation mobile sous charge, ce qui ne doit pas faire échouer l'audit.
      await page
        .screenshot({ path: testInfo.outputPath(`${path.replace(/\W/g, "_") || "home"}.png`), fullPage: true })
        .catch(() => undefined);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();
      const serious = results.violations.filter((v) => ["serious", "critical"].includes(v.impact ?? ""));
      expect(
        serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`),
      ).toEqual([]);
    });
  }

  test("lien d'évitement vers le contenu", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const skip = page.getByRole("link", { name: "Aller au contenu principal" });
    await expect(skip).toBeFocused();
    await expect(skip).toBeVisible();
  });

  test("changement de langue sur la même page", async ({ page, isMobile }) => {
    await page.goto("/charte-graphique");
    // Sur mobile, le choix de la langue se trouve dans le menu.
    const scope = isMobile ? page.getByRole("dialog") : page.getByRole("banner");
    if (isMobile) await page.getByRole("button", { name: "Ouvrir le menu" }).click();
    await scope.getByRole("navigation", { name: "Langue" }).getByRole("link", { name: "en" }).click();
    await expect(page).toHaveURL(/\/en\/charte-graphique$/);
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
  });
});

test.describe("navigation", () => {
  test("menu principal (grand écran)", async ({ page, isMobile }) => {
    test.skip(isMobile, "menu mobile testé séparément");
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Menu principal" });
    await expect(nav.getByRole("link", { name: "Destinations" })).toBeVisible();
    await nav.getByRole("button", { name: "Plus" }).click();
    await expect(page.getByRole("menuitem", { name: "Médiathèque" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Demander un devis" }).first()).toBeVisible();
  });

  test("menu principal sur une seule ligne dès 1280 px", async ({ page, isMobile }) => {
    test.skip(isMobile, "grand écran uniquement");
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");
    const nav = page.getByRole("navigation", { name: "Menu principal" });
    const heights = await nav.getByRole("listitem").evaluateAll((items) =>
      items.map((item) => item.getBoundingClientRect().height),
    );
    expect(Math.max(...heights)).toBeLessThan(48);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });

  test("menu mobile : ouverture, contenu, fermeture au clavier", async ({ page, isMobile }, testInfo) => {
    test.skip(!isMobile, "réservé au mobile");
    await page.goto("/");
    const trigger = page.getByRole("button", { name: "Ouvrir le menu" });
    await trigger.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("link", { name: "Location de véhicules" })).toBeVisible();
    await expect(dialog.getByRole("link", { name: "Demander un devis" })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath("menu-mobile.png") });
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(trigger).toBeFocused();
  });

  // Un test par page : la liste s'allonge à chaque phase.
  for (const path of PAGES) {
    test(`pas de défilement horizontal : ${path}`, async ({ page }) => {
      await page.goto(path);
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(0);
    });
  }
});
