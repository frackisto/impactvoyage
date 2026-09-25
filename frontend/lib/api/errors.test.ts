import { describe, expect, it } from "vitest";

import { ApiError, toApiError } from "./errors";

describe("toApiError", () => {
  it("lit le format d'erreur unique du backend", () => {
    const error = toApiError(409, {
      error: { code: "not_available", message: "Plus de places.", details: { seats_left: 2 } },
    });
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 409, code: "not_available", message: "Plus de places." });
    expect(error.details).toEqual({ seats_left: 2 });
  });

  it("donne les erreurs par champ pour les formulaires", () => {
    const error = toApiError(400, {
      error: {
        code: "validation_error",
        message: "Données invalides.",
        details: { email: ["Adresse invalide."], consent: ["Obligatoire."] },
      },
    });
    expect(error.fieldErrors()).toEqual({ email: "Adresse invalide.", consent: "Obligatoire." });
  });

  it("reste utilisable face à une réponse inattendue", () => {
    expect(toApiError(502, "<html>Bad gateway</html>").code).toBe("unexpected_error");
  });
});
