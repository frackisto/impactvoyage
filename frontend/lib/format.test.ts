import { describe, expect, it } from "vitest";

import { displayMoney, formatAmount, formatRating } from "./format";
import { isActive } from "./navigation";

// Intl utilise des espaces insécables : on les normalise pour comparer.
const plain = (text: string) => text.replace(/[  ]/g, " ");

describe("format", () => {
  it("formate le FCFA sans décimales et l'euro avec", () => {
    expect(plain(formatAmount("150000.00", "XOF", "fr"))).toBe("150 000 F CFA");
    expect(plain(formatAmount("228.67", "EUR", "fr"))).toBe("228,67 €");
    expect(formatAmount("228.67", "EUR", "en")).toBe("€228.67");
  });

  it("affiche la conversion en priorité et garde le prix d'origine", () => {
    const money = { amount: "150000.00", currency: "XOF", display: { amount: "228.67", currency: "EUR" } };
    const shown = displayMoney(money, "fr");
    expect(plain(shown.text)).toBe("228,67 €");
    expect(plain(shown.original ?? "")).toBe("150 000 F CFA");
    expect(displayMoney({ amount: "1000", currency: "XOF" }, "fr").original).toBeNull();
  });

  it("formate une note selon la langue", () => {
    expect(formatRating(4.56, "fr")).toBe("4,6");
    expect(formatRating(4.56, "en")).toBe("4.6");
  });
});

describe("isActive", () => {
  it("reconnaît la rubrique courante, y compris ses sous-pages", () => {
    expect(isActive("/", "/")).toBe(true);
    expect(isActive("/", "/destinations")).toBe(false);
    expect(isActive("/destinations", "/destinations/cote-divoire")).toBe(true);
    expect(isActive("/circuits/nationaux", "/circuits/decouverte-assinie")).toBe(true);
    expect(isActive("/hotels", "/hotels-luxe")).toBe(false);
    expect(isActive("/hotels", "/residences/studio-yopougon")).toBe(true);
  });
});
