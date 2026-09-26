import { describe, expect, it } from "vitest";

import { resultHref, searchHref } from "./search";

describe("recherche", () => {
  it("mène chaque type de résultat à sa page", () => {
    expect(resultHref({ type: "tour", slug: "dubai-ville-des-records" })).toBe("/circuits/dubai-ville-des-records");
    expect(resultHref({ type: "vehicle", slug: "demo-suzuki-vitara" })).toBe("/vehicules/demo-suzuki-vitara");
  });

  it("construit le lien des résultats", () => {
    expect(searchHref("  grand bassam ")).toBe("/recherche?q=grand+bassam");
    expect(searchHref("dubai", "hotel")).toBe("/recherche?q=dubai&type=hotel");
  });
});
