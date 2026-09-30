import { expect, test } from "@playwright/test";

/**
 * Sécurité (Phase 23) : politique de sécurité du contenu (CSP) à nonce sur les pages,
 * sans aucune violation lors d'une visite ; relais vers Django limité à /api/v1 ;
 * envois refusés depuis un autre site. Suppose les données de démonstration chargées.
 */

test.describe("politique de sécurité du contenu", () => {
  test("chaque page a sa CSP avec un nonce propre", async ({ request }) => {
    const first = await request.get("/");
    const second = await request.get("/contact");
    const csp = first.headers()["content-security-policy"];
    expect(csp).toContain("'strict-dynamic'");
    expect(csp).toContain("frame-ancestors 'none'");
    const scriptSrc = csp.split(";").find((directive) => directive.trim().startsWith("script-src"));
    expect(scriptSrc).not.toContain("unsafe-inline");
    const nonce = (value: string | undefined) => value?.match(/'nonce-([^']+)'/)?.[1];
    expect(nonce(csp)).toBeTruthy();
    expect(nonce(second.headers()["content-security-policy"])).not.toBe(nonce(csp));
    // Les scripts de Next.js portent le nonce de la réponse.
    const html = await first.text();
    expect(html).toContain(`nonce="${nonce(csp)}"`);
    expect(first.headers()["cross-origin-opener-policy"]).toBe("same-origin");
  });

  test("les routes /api n'autorisent rien à charger", async ({ request }) => {
    const response = await request.get("/api/backend/tours");
    expect(response.headers()["content-security-policy"]).toBe("default-src 'none'; frame-ancestors 'none'");
  });

  for (const path of ["/", "/circuits/dubai-ville-des-records", "/contact", "/devis", "/en/hotels"]) {
    test(`aucune violation de la CSP sur ${path}`, async ({ page }) => {
      const violations: string[] = [];
      page.on("console", (message) => {
        if (/Content Security Policy|Content-Security-Policy/i.test(message.text())) violations.push(message.text());
      });
      await page.addInitScript(() => {
        document.addEventListener("securitypolicyviolation", (event) => {
          console.error(`Content-Security-Policy: ${event.violatedDirective} ${event.blockedURI}`);
        });
      });
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      // Navigation côté client (scripts chargés dynamiquement par Next.js).
      await page.locator("footer a[href^='/']").first().click();
      await page.waitForLoadState("networkidle");
      expect(violations).toEqual([]);
    });
  }
});

test.describe("relais vers Django", () => {
  test.skip(({ isMobile }) => isMobile, "pas de rendu : un seul profil suffit");

  test("un chemin encodé ne sort jamais de /api/v1", async ({ request }) => {
    for (const path of [
      "/api/backend/x%2F..%2F..%2F..%2Fadmin%2Flogin",
      // Double encodage : Next.js décode une fois, « %2e%2e » arrive tel quel.
      "/api/backend/%252e%252e/%252e%252e/admin/login",
      "/api/backend/tours%5C..%5C..%5Cadmin",
    ]) {
      const response = await request.get(path);
      expect(response.status(), path).toBe(404);
      expect(await response.text()).not.toContain("<html");
    }
    expect((await request.get("/api/backend/tours")).ok()).toBeTruthy();
  });

  test("un envoi depuis un autre site est refusé", async ({ request }) => {
    const response = await request.post("/api/backend/contact", {
      headers: { Origin: "https://evil.example" },
      data: { name: "Robot", email: "robot@example.com", subject: "Spam", message: "Message indésirable." },
    });
    expect(response.status()).toBe(403);
    expect((await response.json()).error.code).toBe("forbidden_origin");

    const login = await request.post("/api/auth/login", {
      headers: { Origin: "https://evil.example" },
      data: { email: "a@example.com", password: "x" },
    });
    expect(login.status()).toBe(403);
  });
});
