import { describe, expect, it } from "vitest";

import { galleryLayout } from "./gallery";

describe("galleryLayout", () => {
  it("met la première photo en avant seulement si la grille reste pleine", () => {
    expect(galleryLayout(3)).toEqual({ columns: "sm:grid-cols-3", feature: true });
    expect(galleryLayout(5).feature).toBe(true);
    expect(galleryLayout(6)).toEqual({ columns: "sm:grid-cols-3", feature: true });
    expect(galleryLayout(4)).toEqual({ columns: "lg:grid-cols-4", feature: false });
    expect(galleryLayout(2).feature).toBe(false);
    expect(galleryLayout(1)).toEqual({ columns: "grid-cols-1", feature: false });
  });
});
