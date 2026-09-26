/**
 * Erreur API au format unique du backend :
 * {"error": {"code": "not_available", "message": "…", "details": {…}}}
 */
export type ApiErrorBody = {
  error: { code: string; message: string; details: Record<string, unknown> };
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** Messages d'erreur par champ, pour React Hook Form (validation_error). */
  fieldErrors(): Record<string, string> {
    const result: Record<string, string> = {};
    for (const [field, value] of Object.entries(this.details)) {
      const first = Array.isArray(value) ? value[0] : value;
      if (typeof first === "string") result[field] = first;
    }
    return result;
  }
}

function isApiErrorBody(body: unknown): body is ApiErrorBody {
  if (!body || typeof body !== "object" || !("error" in body)) return false;
  const error = (body as { error: unknown }).error;
  return !!error && typeof error === "object" && "code" in error && "message" in error;
}

export function toApiError(status: number, body: unknown): ApiError {
  if (isApiErrorBody(body)) {
    const { code, message, details } = body.error;
    return new ApiError(status, code, message, details ?? {});
  }
  return new ApiError(status, "unexpected_error", "Une erreur inattendue est survenue.");
}

/** Résultat de la requête, ou null si la ressource n'existe pas (404) ; les autres erreurs remontent. */
export async function nullIfNotFound<T>(request: Promise<T>): Promise<T | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
