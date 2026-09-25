import { afterEach, describe, expect, it, vi } from "vitest";

import { decodeJwtPayload, isTokenExpired } from "./jwt";

function fakeJwt(payload: object) {
  const encode = (value: object) =>
    btoa(JSON.stringify(value)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `${encode({ alg: "HS256" })}.${encode(payload)}.signature`;
}

describe("jwt", () => {
  afterEach(() => vi.useRealTimers());

  it("lit le contenu d'un jeton (base64url)", () => {
    expect(decodeJwtPayload(fakeJwt({ role: "CLIENT", name: "Awa Koné" }))).toEqual({
      role: "CLIENT",
      name: "Awa Koné",
    });
    expect(decodeJwtPayload("pas-un-jeton")).toBeNull();
  });

  it("considère un jeton expiré avec une marge de sécurité", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-01T12:00:00Z"));
    const now = Date.now() / 1000;
    expect(isTokenExpired(fakeJwt({ exp: now + 600 }))).toBe(false);
    expect(isTokenExpired(fakeJwt({ exp: now + 10 }))).toBe(true); // < 30 s
    expect(isTokenExpired(fakeJwt({ exp: now + 10 }), 0)).toBe(false);
    expect(isTokenExpired(undefined)).toBe(true);
    expect(isTokenExpired(fakeJwt({}))).toBe(true);
  });
});
