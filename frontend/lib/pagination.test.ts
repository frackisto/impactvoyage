import { describe, expect, it } from "vitest";

import { pageHref, pageNumbers } from "./pagination";

describe("pageNumbers", () => {
  it("affiche toutes les pages quand il y en a peu", () => {
    expect(pageNumbers(1, 3)).toEqual([1, 2, 3]);
  });

  it("résume les longues listes autour de la page courante", () => {
    expect(pageNumbers(6, 12)).toEqual([1, "gap", 5, 6, 7, "gap", 12]);
    expect(pageNumbers(1, 12)).toEqual([1, 2, "gap", 12]);
    expect(pageNumbers(12, 12)).toEqual([1, "gap", 11, 12]);
  });
});

describe("pageHref", () => {
  it("conserve les filtres non vides et omet la première page", () => {
    expect(pageHref("/destinations", { continent: "AFRIQUE", search: undefined }, 1)).toBe(
      "/destinations?continent=AFRIQUE",
    );
    expect(pageHref("/destinations", { search: "lahou" }, 3)).toBe("/destinations?search=lahou&page=3");
    expect(pageHref("/destinations", {}, 1)).toBe("/destinations");
  });
});
