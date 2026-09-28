import { expect, test } from "@playwright/test";

/**
 * Système de devis (Phase 17). Suppose la démonstration chargée côté Django :
 *   python manage.py seed_demo
 * DV-DEMO-000001 : proposition envoyée (Dubaï) ; DV-DEMO-000002 : en cours d'étude.
 * L'envoi et la réponse sont simulés (page.route) : les données de démonstration ne
 * changent pas et la limite de 5 demandes par heure n'est pas atteinte.
 */
const SENT = "/devis/DV-DEMO-000001?token=7e57d3a0-0000-4000-8000-000000000001";
const IN_PROGRESS = "/devis/DV-DEMO-000002?token=7e57d3a0-0000-4000-8000-000000000002";

async function fillContact(page: import("@playwright/test").Page) {
  await page.getByLabel("Prénom").fill("Awa");
  await page.getByLabel("Nom", { exact: true }).fill("Koné");
  await page.getByLabel("Adresse email").fill("awa@example.com");
  await page.getByLabel("Téléphone").fill("+225 07 00 00 00 01");
  await page.getByRole("checkbox", { name: /J'accepte qu'Impact Voyage/ }).check();
}

test.describe("demande de devis", () => {
  test("préremplie depuis un circuit, erreurs puis envoi", async ({ page }) => {
    await page.goto("/devis?tour=dubai-ville-des-records");
    await expect(page.getByRole("heading", { level: 1, name: "Demande de devis" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Dubaï, la ville de tous les records" })).toHaveAttribute(
      "href",
      "/circuits/dubai-ville-des-records",
    );
    await expect(page.getByLabel("Destination", { exact: true })).toHaveValue("dubai");
    await expect(page.getByRole("checkbox", { name: "Circuit organisé" })).toBeChecked();

    // Contrôles du navigateur : champs obligatoires et consentement.
    await page.getByRole("button", { name: "Envoyer ma demande" }).click();
    await expect(page.getByText("Ce champ est obligatoire.").first()).toBeVisible();
    await expect(page.getByText("Votre accord est nécessaire pour envoyer la demande.")).toBeVisible();
    await expect(page.getByLabel("Prénom")).toBeFocused();

    // Erreur renvoyée par Django : affichée sous le champ concerné.
    let payload: Record<string, unknown> = {};
    await page.route("**/api/backend/quotes", async (route) => {
      payload = route.request().postDataJSON();
      if (payload.phone === "+225 07 00 00 00 01") {
        return route.fulfill({
          status: 400,
          json: { error: { code: "validation_error", message: "Données invalides.", details: { phone: ["Numéro inconnu."] } } },
        });
      }
      return route.fulfill({ status: 201, json: { reference: "DV-2026-000042", status: "NOUVELLE" } });
    });
    await fillContact(page);
    await page.getByRole("button", { name: "Envoyer ma demande" }).click();
    await expect(page.getByText("Numéro inconnu.")).toBeVisible();
    await expect(page.getByRole("alert").filter({ hasText: "Certains champs sont à corriger." })).toBeVisible();
    expect(payload).toMatchObject({
      destination: "dubai",
      destination_text: "",
      source_tour: "dubai-ville-des-records",
      services_requested: ["CIRCUIT"],
      adults: 1,
      consent: true,
      website: "",
    });

    await page.getByLabel("Téléphone").fill("+225 07 00 00 00 02");
    await page.getByRole("button", { name: "Envoyer ma demande" }).click();
    const success = page.getByRole("status").filter({ hasText: "Demande envoyée !" });
    await expect(success).toBeFocused();
    await expect(success).toContainText("votre demande DV-2026-000042 a bien été reçue");
  });

  test("hôtel et dates repris, destination libre", async ({ page }) => {
    await page.goto("/devis?hotel=hotel-lagune-plateau&start=2027-03-01&end=2027-03-04&travelers=2");
    await expect(page.getByText("Du 1 mars 2027 au 4 mars 2027 · 2 voyageurs")).toBeVisible();
    await expect(page.getByLabel("Date de départ")).toHaveValue("2027-03-01");
    await expect(page.getByLabel("Adultes")).toHaveValue("2");
    await expect(page.getByRole("checkbox", { name: "Hébergement", exact: true })).toBeChecked();

    // « Autre destination » : la saisie libre devient obligatoire.
    await page.getByLabel("Destination", { exact: true }).selectOption({ label: "Autre destination…" });
    await fillContact(page);
    await page.getByRole("button", { name: "Envoyer ma demande" }).click();
    await expect(page.getByText("Indiquez la destination souhaitée.")).toBeVisible();
  });
});

test.describe("suivi du devis", () => {
  test("proposition envoyée : accepter après confirmation", async ({ page }) => {
    await page.goto(SENT);
    await expect(page.getByRole("heading", { level: 1, name: "Devis DV-DEMO-000001" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Votre demande : proposition envoyée/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Notre proposition" })).toBeVisible();
    await expect(page.getByText(/Proposition valable jusqu'au/)).toBeVisible();

    // Décliner demande un motif facultatif et peut être annulé.
    await page.getByRole("button", { name: "Décliner" }).click();
    await expect(page.getByLabel("Pouvez-vous nous dire pourquoi ? (facultatif)")).toBeVisible();
    await page.getByRole("button", { name: "Annuler" }).click();

    await page.route("**/api/backend/quotes/DV-DEMO-000001/accept", (route) =>
      route.fulfill({ json: { reference: "IV-2026-000123", status: "PENDING" } }),
    );
    await page.getByRole("button", { name: "Accepter la proposition" }).click();
    await page.getByRole("button", { name: "Oui, j'accepte" }).click();
    await expect(page.getByRole("status").filter({ hasText: "IV-2026-000123" })).toContainText("Proposition acceptée");
  });

  test("demande en cours, en anglais", async ({ page }) => {
    await page.goto(`/en${IN_PROGRESS}`);
    await expect(page.getByRole("heading", { name: /Your request: under review/ })).toBeVisible();
    await expect(page.getByText("An advisor is preparing your proposal.", { exact: false })).toBeVisible();
    await expect(page.getByRole("button", { name: "Accept the proposal" })).toHaveCount(0);
  });

  test("lien invalide, jamais indexé", async ({ page }) => {
    await page.goto("/devis/DV-DEMO-000001?token=faux");
    await expect(page.getByRole("heading", { level: 1, name: "Lien de suivi invalide" })).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
    await expect(page.getByRole("link", { name: "Nouvelle demande de devis" })).toHaveAttribute("href", "/devis");
  });
});
