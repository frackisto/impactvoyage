/** Paramètres d'URL tels que Next.js les passe aux pages (searchParams). */
export type SearchParams = Record<string, string | string[] | undefined>;

/** Première valeur d'un paramètre, sans espaces ; undefined si absente ou vide. */
export function param(params: SearchParams, key: string): string | undefined {
  const value = params[key];
  return (Array.isArray(value) ? value[0] : value)?.trim() || undefined;
}

/** Entier dans [min, max] ; undefined sinon (une valeur invalide est ignorée, pas une erreur). */
export function intParam(params: SearchParams, key: string, min: number, max: number): number | undefined {
  const value = Number(param(params, key));
  return Number.isInteger(value) && value >= min && value <= max ? value : undefined;
}

/** Date AAAA-MM-JJ valide ; undefined sinon. */
export function dateParam(params: SearchParams, key: string): string | undefined {
  const value = param(params, key);
  return value && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value)) ? value : undefined;
}

/** Page demandée (1 par défaut). */
export function pageParam(params: SearchParams): number {
  return intParam(params, "page", 1, 10_000) ?? 1;
}
