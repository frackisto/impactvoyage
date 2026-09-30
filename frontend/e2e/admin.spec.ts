import { expect, test } from "@playwright/test";

/**
 * Backoffice (Phases 19 et 23) : servi par Django à une adresse non standard en
 * production (ADMIN_URL_PATH). Le site ne la révèle pas : /admin y est une page
 * introuvable, sans redirection vers le backoffice. (Comme toute page inconnue, elle
 * est servie en streaming avec le statut 200 et la balise noindex.)
 */
test.describe("le site ne mène pas au backoffice", () => {
  for (const path of ["/admin", "/admin/login"]) {
    test(`${path} : page introuvable, sans redirection`, async ({ request }) => {
      const response = await request.get(path, { maxRedirects: 0 });
      expect(response.status()).not.toBe(307);
      expect(response.headers().location).toBeUndefined();
      const html = await response.text();
      expect(html).toContain('name="robots" content="noindex"');
      expect(html).not.toContain("localhost:8000");
    });
  }
});
