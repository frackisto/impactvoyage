import { describe, expect, it } from "vitest";

import { inPeriods, monthWeeks } from "./calendar";

describe("calendrier", () => {
  it("aligne le 1er du mois sur le bon jour (lundi en premier)", () => {
    // 1er octobre 2026 : un jeudi.
    const { weeks } = monthWeeks("2026-10-15");
    expect(weeks[0]).toEqual([null, null, null, "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"]);
    expect(weeks.flat().filter(Boolean)).toHaveLength(31);
    expect(weeks.every((week) => week.length === 7)).toBe(true);
  });

  it("passe à l'année suivante", () => {
    expect(monthWeeks("2026-12-20", 1).first.toISOString().slice(0, 10)).toBe("2027-01-01");
  });

  it("exclut le jour de fin d'une période", () => {
    const periods = [["2026-10-05", "2026-10-09"]];
    expect(inPeriods("2026-10-05", periods)).toBe(true);
    expect(inPeriods("2026-10-08", periods)).toBe(true);
    expect(inPeriods("2026-10-09", periods)).toBe(false);
  });
});
