import { expect, test } from "@playwright/test";

/**
 * Pages hors plan de développement : services, offres, visas, transport,
 * médiathèque, blog, à propos, contact et pages légales. Suppose la
 * démonstration chargée côté Django (python manage.py seed_demo).
 */

test.describe("services et offres", () => {
  test("services : sommaire, tarifs et liens vers le devis", async ({ page }) => {
    await page.goto("/services");
    await expect(page.getByRole("heading", { level: 1, name: "Nos services" })).toBeVisible();
    const visa = page.locator("article#visa-et-formalites");
    await expect(visa.getByRole("heading", { name: "Visa et formalités" })).toBeVisible();
    await expect(visa.getByRole("table")).toContainText("Prise de rendez-vous — France");
    await expect(visa.getByRole("link", { name: /Demander un devis/ })).toHaveAttribute("href", "/devis?service=VISA");
    await expect(visa.getByRole("link", { name: /Voir l'offre/ })).toHaveAttribute("href", "/visa");
  });

  test("offres : filtre par type, fiche et demande préremplie", async ({ page }) => {
    await page.goto("/offres");
    const results = page.getByRole("heading", { name: /offres? en cours$/ });
    await expect(results).toHaveText("3 offres en cours");
    const filters = page.getByRole("search", { name: "Filtrer les offres" });
    if (!(await filters.isVisible())) await page.getByRole("button", { name: /Filtres/ }).click();
    await filters.getByLabel("Type d'offre").selectOption("CIRCUIT");
    await expect(page).toHaveURL(/\/offres\?offer_type=CIRCUIT$/);
    await expect(results).toHaveText("1 offre en cours");

    await page.getByRole("link", { name: "Week-end à Mondoukou à prix doux" }).click();
    await expect(page.getByRole("heading", { level: 1, name: "Week-end à Mondoukou à prix doux" })).toBeVisible();
    // 4 places : le badge « Dernières places » s'impose.
    await expect(page.getByText("Dernières places").first()).toBeVisible();
    await expect(page.getByText("−17 %")).toBeVisible();
    await expect(page.getByRole("link", { name: /Voir la fiche/ })).toHaveAttribute("href", "/circuits/week-end-balneaire-mondoukou");
    await page.getByRole("link", { name: "Profiter de l'offre" }).click();
    await expect(page).toHaveURL(/\/devis\?offer=week-end-mondoukou-prix-doux$/);
    await expect(page.getByRole("link", { name: "Week-end à Mondoukou à prix doux" })).toBeVisible();
    await expect(page.getByRole("checkbox", { name: "Circuit organisé" })).toBeChecked();
  });
});

test.describe("visas et transport", () => {
  test("visas : filtre par pays puis fiche pays", async ({ page }) => {
    await page.goto("/visa");
    await expect(page.getByRole("heading", { name: "6 pays" })).toBeVisible();
    await page.goto("/visa?destination_country_code=FR");
    await expect(page.getByRole("heading", { name: "1 pays" })).toBeVisible();
    await page.getByRole("link", { name: "Visa France" }).click();
    await expect(page).toHaveURL(/\/visa\/france$/);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Visa France");
    await expect(page.getByText("Formules proposées pour les ressortissants de : Côte d’Ivoire.")).toBeVisible();
    await expect(page.getByRole("link", { name: "Être accompagné" })).toHaveAttribute("href", "/devis?service=VISA");
  });

  test("visa : pays inconnu → page introuvable", async ({ page }) => {
    await page.goto("/visa/atlantide");
    await expect(page.getByRole("heading", { name: "Page introuvable" })).toBeVisible();
    await expect(page.locator('meta[name="robots"][content="noindex"]').first()).toBeAttached();
  });

  test("transport : recherche de l'accueil, filtres et devis prérempli", async ({ page }) => {
    await page.goto("/transport?origin=abidjan&passengers=6&date=2027-01-15");
    await expect(page.getByRole("heading", { name: "2 services" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Navette Abidjan – Grand-Bassam" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Transfert aéroport d'Abidjan" })).toHaveCount(0);
    const quote = page.getByRole("main").getByRole("link", { name: "Demander un devis" }).first();
    await expect(quote).toHaveAttribute("href", "/devis?service=TRANSPORT&start=2027-01-15&travelers=6");
    await quote.click();
    await expect(page.getByLabel("Date de départ")).toHaveValue("2027-01-15");
    await expect(page.getByLabel("Adultes")).toHaveValue("6");
    await expect(page.getByRole("checkbox", { name: "Transferts et transport" })).toBeChecked();
  });
});

test.describe("médiathèque et blog", () => {
  test("albums par catégorie et visionneuse", async ({ page }) => {
    await page.goto("/mediatheque");
    await expect(page.getByRole("heading", { name: "3 albums" })).toBeVisible();
    await page.getByRole("navigation", { name: "Catégories d'albums" }).getByRole("link", { name: "L'agence" }).click();
    await expect(page).toHaveURL(/\/mediatheque\?category=agence$/);
    await expect(page.getByRole("heading", { name: "1 album" })).toBeVisible();

    await page.goto("/mediatheque/dubai-en-images");
    await expect(page.getByRole("heading", { name: "4 photos" })).toBeVisible();
    await page.getByRole("button", { name: /Agrandir|photo 1/i }).first().click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("blog : catégories, article structuré, mots-clés et JSON-LD", async ({ page }) => {
    await page.goto("/blog");
    await expect(page.getByRole("heading", { name: "3 articles" })).toBeVisible();
    await page.getByRole("link", { name: "Que mettre dans sa valise pour Dubaï ?" }).click();
    await expect(page.getByRole("heading", { level: 1, name: "Que mettre dans sa valise pour Dubaï ?" })).toBeVisible();
    const article = page.getByRole("article", { name: "Que mettre dans sa valise pour Dubaï ?" });
    await expect(article.getByRole("heading", { level: 2, name: "Les indispensables" })).toBeVisible();
    await expect(article.getByRole("listitem")).toHaveCount(4);
    const jsonLd = JSON.parse((await page.locator('script[type="application/ld+json"]').textContent()) ?? "{}");
    expect(jsonLd["@graph"][0]["@type"]).toBe("BlogPosting");

    await page.getByRole("list", { name: "Mots-clés" }).getByRole("link", { name: "Dubaï" }).click();
    await expect(page).toHaveURL(/\/blog\?tag=dubai$/);
    await expect(page.getByText("Articles avec le mot-clé « Dubaï »")).toBeVisible();
    await expect(page.getByRole("heading", { name: "1 article" })).toBeVisible();
  });
});

test.describe("agence et pages légales", () => {
  test("à propos : présentation de l'agence et coordonnées", async ({ page }) => {
    await page.goto("/a-propos");
    await expect(page.getByRole("heading", { level: 1, name: "À propos" })).toBeVisible();
    await expect(page.getByText(/IMPACT VOYAGE ET LOGISTIQUE SARLP est une agence/)).toBeVisible();
    await expect(page.getByRole("link", { name: "Visa et formalités" })).toHaveAttribute("href", "/services#visa-et-formalites");
    await expect(page.getByRole("main").getByRole("link", { name: /\+225 27 23 22 88 57/ })).toHaveAttribute("href", "tel:+2252723228857");
  });

  test("contact : validation puis envoi", async ({ page }) => {
    await page.goto("/contact");
    await page.getByRole("button", { name: "Envoyer le message" }).click();
    await expect(page.getByText("Choisissez l'objet de votre message.")).toBeVisible();
    await expect(page.getByLabel("Nom complet")).toBeFocused();

    let payload: Record<string, unknown> = {};
    await page.route("**/api/backend/contact", async (route) => {
      payload = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: { message: "ok" } });
    });
    await page.getByLabel("Nom complet").fill("Awa Koné");
    await page.getByLabel("Adresse email").fill("awa@example.com");
    await page.getByLabel("Objet").selectOption({ label: "Partenariat" });
    await page.getByLabel("Message").fill("Bonjour, nous souhaitons proposer un partenariat.");
    await page.getByRole("button", { name: "Envoyer le message" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Message envoyé !" })).toBeFocused();
    expect(payload).toMatchObject({ name: "Awa Koné", subject: "Partenariat", phone: "", website: "" });
  });

  test("pages légales : sommaire, coordonnées de l'agence, liens croisés", async ({ page }) => {
    await page.goto("/mentions-legales");
    await expect(page.getByRole("heading", { level: 1, name: "Mentions légales" })).toBeVisible();
    await expect(page.getByText("Le site est édité par Impact Voyage et Logistique SARLP", { exact: false })).toBeVisible();
    await page.getByRole("navigation", { name: "Sommaire" }).getByRole("link", { name: "4. Propriété intellectuelle" }).click();
    await expect(page).toHaveURL(/#section-4$/);
    await page.getByRole("navigation", { name: "Autres documents" }).getByRole("link", { name: "Politique de confidentialité" }).click();
    await expect(page.getByRole("heading", { level: 2, name: "6. Cookies" })).toBeVisible();
    await page.goto("/en/conditions-generales");
    await expect(page.getByRole("heading", { level: 1, name: "Terms and conditions" })).toBeVisible();
  });

  test("pied de page : liens vers les nouvelles rubriques", async ({ page }) => {
    await page.goto("/");
    const footer = page.getByRole("contentinfo");
    for (const [name, href] of [["Visas", "/visa"], ["Transport", "/transport"], ["Blog", "/blog"], ["Contact", "/contact"]]) {
      await expect(footer.getByRole("link", { name, exact: true })).toHaveAttribute("href", href);
    }
  });
});
