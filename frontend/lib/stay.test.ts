import { describe, expect, it } from "vitest";

import { multiplyMoney } from "./format";
import { nights, parseStay, stayQuery } from "./stay";

describe("séjour", () => {
  it("compte les nuits", () => {
    expect(nights("2026-11-01", "2026-11-04")).toBe(3);
    expect(nights("2026-11-04", "2026-11-01")).toBe(0);
    expect(nights(undefined, "2026-11-01")).toBe(0);
  });

  it("ignore une période invalide mais garde voyageurs et chambres", () => {
    expect(parseStay({ start: "2026-11-04", end: "2026-11-01", travelers: "3" })).toEqual({
      travelers: 3,
      rooms: undefined,
    });
    expect(parseStay({ available_from: "2026-11-01", available_to: "2026-11-03", rooms: "2" }, {
      start: "available_from",
      end: "available_to",
    })).toEqual({ start: "2026-11-01", end: "2026-11-03", travelers: undefined, rooms: 2 });
  });

  it("n'écrit dans l'URL que les valeurs utiles", () => {
    expect(stayQuery({ start: "2026-11-01", end: "2026-11-03", rooms: 1 })).toEqual({
      start: "2026-11-01", end: "2026-11-03", travelers: undefined, rooms: undefined,
    });
  });

  it("multiplie un montant et sa conversion", () => {
    const money = { amount: "45000.00", currency: "XOF", display: { amount: "68.60", currency: "EUR" } };
    expect(multiplyMoney(money, 3)).toEqual({
      amount: "135000.00", currency: "XOF", display: { amount: "205.80", currency: "EUR" },
    });
  });
});
