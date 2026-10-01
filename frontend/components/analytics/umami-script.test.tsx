import { afterEach, describe, expect, it, vi } from "vitest";

import { UmamiScript } from "./umami-script";

vi.mock("next/headers", () => ({
  headers: async () => new Headers({ "x-nonce": "nonce-de-test" }),
}));

describe("UmamiScript", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("ne charge rien sans identifiant de site", async () => {
    vi.stubEnv("UMAMI_WEBSITE_ID", "");
    expect(await UmamiScript()).toBeNull();
  });

  it("charge le script servi par le site, avec le nonce de la page", async () => {
    vi.stubEnv("UMAMI_WEBSITE_ID", "1e3d900d-e224-4f9d-b004-d80489dc93e6");
    const script = await UmamiScript();
    expect(script?.props).toMatchObject({
      src: "/stats/script.js",
      nonce: "nonce-de-test",
      "data-website-id": "1e3d900d-e224-4f9d-b004-d80489dc93e6",
      "data-domains": "localhost",
      "data-do-not-track": "true",
    });
  });
});
