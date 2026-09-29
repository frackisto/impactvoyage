import { expect, test, type Page } from "@playwright/test";

/**
 * Réservation en ligne (Phase 18). Suppose la démonstration chargée côté Django :
 *   python manage.py seed_demo
 * IV-DEMO-000001 : demande de réservation reçue (villa à Grand-Bassam), à lien fixe.
 * L'envoi et l'annulation sont simulés (page.route) : les données de démonstration ne
 * changent pas et la limite de 10 demandes par heure n'est pas atteinte.
 */
const DEMO_TOKEN = "7e57d3a0-0000-4000-8000-000000000101";
const DEMO = `/reservation/IV-DEMO-000001?token=${DEMO_TOKEN}`;

const inDays = (days: number) => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
};

async function fillContact(page: Page) {
  await page.getByLabel("Nom et prénom").fill("Awa Koné");
  await page.getByLabel("Email", { exact: true }).fill("awa@example.com");
  await page.getByLabel("Téléphone").fill("+225 07 00 00 00 01");
  await page.getByRole("checkbox", { name: /J'accepte qu'Impact Voyage/ }).check();
}

test.describe("demande de réservation", () => {
  test("véhicule : de la fiche au suivi, sans aucun prix envoyé", async ({ page }) => {
    const [start, end] = [inDays(20), inDays(23)];
    await page.goto(`/vehicules/demo-suzuki-vitara?start=${start}&end=${end}`);
    await page.getByRole("status").filter({ hasText: "Disponible du" }).getByRole("link", { name: "Réserver" }).click();

    await expect(page).toHaveURL(`/reservation?vehicle=demo-suzuki-vitara&start=${start}&end=${end}`);
    await expect(page.getByRole("heading", { level: 1, name: "Demande de réservation" })).toBeVisible();
    const offer = page.getByRole("region", { name: "Suzuki Vitara" });
    await expect(offer).toContainText("Location de véhicule");
    await expect(offer).toContainText("3 jours");
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);

    // Contrôles du navigateur : champs obligatoires et consentement.
    await page.getByRole("button", { name: "Envoyer la demande de réservation" }).click();
    await expect(page.getByText("Ce champ est obligatoire.")).toBeVisible();
    await expect(page.getByText("Votre accord est nécessaire pour envoyer la demande.")).toBeVisible();
    await expect(page.getByLabel("Nom et prénom")).toBeFocused();

    let payload: Record<string, unknown> = {};
    await page.route("**/api/backend/bookings", async (route) => {
      payload = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        json: { reference: "IV-DEMO-000001", access_token: DEMO_TOKEN, status: "REQUESTED" },
      });
    });
    await page.getByLabel("Lieu de prise en charge (facultatif)").fill("Aéroport d'Abidjan");
    await fillContact(page);
    await page.getByRole("button", { name: "Envoyer la demande de réservation" }).click();

    await expect(page).toHaveURL(`${DEMO}&sent=1`);
    await expect(page.getByRole("status").filter({ hasText: "Demande envoyée !" })).toContainText("demo@example.com");
    expect(payload).toEqual({
      contact_name: "Awa Koné",
      contact_email: "awa@example.com",
      contact_phone: "+225 07 00 00 00 01",
      customer_comments: "",
      consent: true,
      website: "",
      items: [
        {
          kind: "vehicle",
          object_id: expect.any(Number),
          start_date: start,
          end_date: end,
          quantity: 1,
          pickup_location: "Aéroport d'Abidjan",
          dropoff_location: "",
        },
      ],
    });
  });

  test("départ de circuit : voyageurs contrôlés, départ complet entre-temps", async ({ page }) => {
    await page.goto("/circuits/dubai-ville-des-records");
    await page.getByRole("link", { name: /Réserver le départ du/ }).first().click();
    await expect(page).toHaveURL(/\/reservation\?tour=dubai-ville-des-records&departure=\d+$/);
    await expect(page.getByRole("region", { name: "Dubaï, la ville de tous les records" })).toContainText(/places restantes/);

    const travelers = page.getByLabel("Nombre de voyageurs");
    await expect(travelers).toHaveValue("1");
    await travelers.fill("99");
    await fillContact(page);
    await page.getByRole("button", { name: "Envoyer la demande de réservation" }).click();
    await expect(page.getByText(/Indiquez un nombre entre 1 et \d+\./)).toBeVisible();

    let payload: { items?: { kind: string; quantity: number }[] } = {};
    await page.route("**/api/backend/bookings", async (route) => {
      payload = route.request().postDataJSON();
      await route.fulfill({
        status: 409,
        json: { error: { code: "not_available", message: "Il ne reste que 1 place(s).", details: { seats_left: 1 } } },
      });
    });
    await travelers.fill("3");
    await page.getByRole("button", { name: "Envoyer la demande de réservation" }).click();
    const alert = page.getByRole("alert").filter({ hasText: "n'est plus disponible aux dates choisies" });
    await expect(alert).toBeVisible();
    await expect(alert.getByRole("link", { name: "Revenir à la fiche pour choisir d'autres dates" })).toHaveAttribute(
      "href",
      "/circuits/dubai-ville-des-records",
    );
    expect(payload.items?.[0]).toMatchObject({ kind: "tour_departure", quantity: 3 });
  });

  test("chambre d'hôtel : type et nombre de chambres repris", async ({ page }) => {
    await page.goto("/hotels/hotel-lagune-plateau?start=2027-03-01&end=2027-03-04&travelers=3");
    await page.getByRole("link", { name: "Réserver la chambre « Suite familiale »" }).click();
    const offer = page.getByRole("region", { name: "Hôtel Lagune Plateau" });
    await expect(offer).toContainText("Suite familiale");
    await expect(offer).toContainText("3 nuits");
    await expect(page.getByLabel("Nombre de chambres")).toHaveValue("1");
    await expect(page.getByText("Jusqu'à 2 selon les disponibilités.")).toBeVisible();
  });

  test("dates manquantes, période déjà réservée, lien sans prestation", async ({ page }) => {
    await page.goto("/reservation?vehicle=demo-suzuki-vitara");
    await expect(page.getByRole("status").filter({ hasText: "Choisissez d'abord vos dates" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Choisir mes dates" })).toHaveAttribute("href", "/vehicules/demo-suzuki-vitara#disponibilites");
    await expect(page.getByRole("button", { name: "Envoyer la demande de réservation" })).toHaveCount(0);

    // La Vitara de démonstration est réservée de J+5 à J+9.
    await page.goto(`/reservation?vehicle=demo-suzuki-vitara&start=${inDays(6)}&end=${inDays(8)}`);
    await expect(page.getByRole("status").filter({ hasText: "n'est pas disponible aux dates choisies" })).toBeVisible();
    await expect(page.getByRole("main").getByRole("link", { name: "Demander un devis" }).first()).toHaveAttribute(
      "href",
      `/devis?vehicle=demo-suzuki-vitara&start=${inDays(6)}&end=${inDays(8)}`,
    );

    await page.goto("/reservation");
    await expect(page.getByRole("heading", { name: "Choisissez une prestation à réserver" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Véhicules" }).last()).toHaveAttribute("href", "/vehicules");
  });
});

test.describe("suivi de la réservation", () => {
  test("demande reçue : prestations et annulation confirmée", async ({ page }) => {
    await page.goto(DEMO);
    await expect(page.getByRole("heading", { level: 1, name: "Réservation IV-DEMO-000001" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Statut : demande reçue/ })).toBeVisible();
    const items = page.getByRole("region", { name: "Prestations réservées" });
    await expect(items.getByRole("link", { name: /Villa familiale à Grand-Bassam/ })).toHaveAttribute(
      "href",
      "/residences/villa-familiale-grand-bassam",
    );
    await expect(items).toContainText(/Arrivée le .*, départ le/);
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);

    // L'agence confirme entre-temps : l'annulation est refusée avec un message clair.
    const bodies: Record<string, unknown>[] = [];
    let confirmed = true;
    await page.route("**/api/backend/bookings/IV-DEMO-000001/cancel", async (route) => {
      bodies.push(route.request().postDataJSON());
      if (confirmed) {
        return route.fulfill({
          status: 409,
          json: { error: { code: "contact_agency", message: "Contactez l'agence.", details: {} } },
        });
      }
      return route.fulfill({ json: { reference: "IV-DEMO-000001", status: "CANCELLED" } });
    });
    await page.getByRole("button", { name: "Annuler ma demande" }).click();
    await page.getByLabel("Motif (facultatif)").fill("Changement de dates");
    await page.getByRole("button", { name: "Oui, annuler" }).click();
    await expect(page.getByRole("alert").filter({ hasText: "vient d'être confirmée" })).toBeVisible();

    confirmed = false;
    await page.getByRole("button", { name: "Annuler ma demande" }).click();
    await page.getByRole("button", { name: "Non, garder ma demande" }).click();
    await page.getByRole("button", { name: "Annuler ma demande" }).click();
    await page.getByRole("button", { name: "Oui, annuler" }).click();
    await expect.poll(() => bodies.length).toBe(2);
    expect(bodies[1]).toEqual({ token: DEMO_TOKEN, reason: "Changement de dates" });
    // La page se recharge (router.refresh) : on attend la fin avant de fermer le navigateur.
    await page.waitForLoadState("networkidle");
  });

  test("en anglais", async ({ page }) => {
    await page.goto(`/en${DEMO}`);
    await expect(page.getByRole("heading", { name: /Status: request received/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "Cancel my request" })).toBeVisible();
  });

  test("lien invalide, jamais indexé", async ({ page }) => {
    await page.goto("/reservation/IV-DEMO-000001?token=faux");
    await expect(page.getByRole("heading", { level: 1, name: "Lien de réservation invalide" })).toBeVisible();
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
    await expect(page.getByRole("main").getByRole("link", { name: "Nous contacter" })).toHaveAttribute("href", "/contact");
  });
});
