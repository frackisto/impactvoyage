import { describe, expect, it } from "vitest";

import { backendPath, contentSecurityPolicy, createNonce, isSameOriginRequest } from "./security";

describe("backendPath", () => {
  it("relaie les chemins de l'API", () => {
    expect(backendPath(["tours"])).toBe("tours/");
    expect(backendPath(["bookings", "IV-2026-0001", "cancel"])).toBe("bookings/IV-2026-0001/cancel/");
  });

  it("refuse tout ce qui pourrait sortir de /api/v1", () => {
    // Segments tels que Next.js les décode : « %2F..%2Fadmin » donne « /../admin ».
    for (const segments of [[], [".."], ["tours", "."], ["x/../../admin"], ["a\\b"], ["%2e%2e"], ["tours", ""], ["a b"]]) {
      expect(backendPath(segments), JSON.stringify(segments)).toBeNull();
    }
  });
});

describe("isSameOriginRequest", () => {
  const request = (method: string, headers: Record<string, string>) =>
    new Request("http://site.test/api/backend/contact", { method, headers });

  it("accepte les lectures et les envois depuis le site", () => {
    expect(isSameOriginRequest(request("GET", { origin: "https://evil.example", host: "site.test" }))).toBe(true);
    expect(isSameOriginRequest(request("POST", { origin: "https://www.impactvoyage.ci", host: "www.impactvoyage.ci" }))).toBe(true);
    // Derrière Nginx : l'hôte public est transmis par X-Forwarded-Host.
    expect(
      isSameOriginRequest(
        request("POST", { origin: "https://www.impactvoyage.ci", host: "frontend:3000", "x-forwarded-host": "www.impactvoyage.ci" }),
      ),
    ).toBe(true);
    // Sans navigateur (curl) : pas de cookie à détourner.
    expect(isSameOriginRequest(request("POST", { host: "site.test" }))).toBe(true);
  });

  it("refuse un envoi depuis un autre site", () => {
    expect(isSameOriginRequest(request("POST", { origin: "https://evil.example", host: "site.test" }))).toBe(false);
    expect(isSameOriginRequest(request("DELETE", { "sec-fetch-site": "cross-site", host: "site.test" }))).toBe(false);
    expect(isSameOriginRequest(request("POST", { origin: "null", host: "site.test" }))).toBe(false);
  });
});

describe("contentSecurityPolicy", () => {
  it("n'autorise que les scripts portant le nonce, et Turnstile", () => {
    const csp = contentSecurityPolicy("abc123");
    expect(csp).toContain("script-src 'self' 'nonce-abc123' 'strict-dynamic' https://challenges.cloudflare.com");
    expect(csp).toContain("frame-src https://challenges.cloudflare.com");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).not.toContain("unsafe-eval");
    expect(csp).not.toContain("upgrade-insecure-requests");
  });

  it("s'adapte au développement et au HTTPS", () => {
    expect(contentSecurityPolicy("n", { dev: true })).toContain("'unsafe-eval'");
    expect(contentSecurityPolicy("n", { https: true })).toContain("upgrade-insecure-requests");
  });

  it("change de nonce à chaque réponse", () => {
    const nonce = createNonce();
    expect(nonce).toMatch(/^[A-Za-z0-9+/]{22}==$/);
    expect(createNonce()).not.toBe(nonce);
  });
});
