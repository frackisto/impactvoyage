import { expect, test } from "@playwright/test";

/**
 * Backoffice (Phase 19) : servi par Django, pas par le site. /admin ouvert sur le
 * site est redirigé vers l'admin Django (ADMIN_URL) au lieu d'afficher une 404.
 */
test.describe("accès au backoffice depuis le site", () => {
  for (const path of ["/admin", "/admin/login"]) {
    test(`${path} redirige vers l'admin Django`, async ({ request }) => {
      const response = await request.get(path, { maxRedirects: 0 });
      expect(response.status()).toBe(307);
      expect(response.headers().location).toMatch(/^http:\/\/localhost:8000\/admin\/(login)?$/);
    });
  }
});
