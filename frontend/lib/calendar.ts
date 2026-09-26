/** Date AAAA-MM-JJ en UTC (mois de 0 à 11, débordements acceptés). */
export const isoDate = (year: number, month: number, day: number) =>
  new Date(Date.UTC(year, month, day)).toISOString().slice(0, 10);

/**
 * Semaines d'un mois, du lundi au dimanche : null pour les cases hors du mois.
 * `offset` mois après le mois de `from` (AAAA-MM-JJ).
 */
export function monthWeeks(from: string, offset = 0) {
  const [year, month] = from.split("-").map(Number);
  const first = new Date(Date.UTC(year, month - 1 + offset, 1));
  const y = first.getUTCFullYear();
  const m = first.getUTCMonth();
  const days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
  const lead = (first.getUTCDay() + 6) % 7; // lundi = 0
  const cells: (string | null)[] = [...Array<null>(lead).fill(null), ...Array.from({ length: days }, (_, d) => isoDate(y, m, d + 1))];
  while (cells.length % 7) cells.push(null);
  return { first, weeks: Array.from({ length: cells.length / 7 }, (_, w) => cells.slice(w * 7, w * 7 + 7)) };
}

/** Vrai si le jour tombe dans l'une des périodes [début, fin). */
export const inPeriods = (day: string, periods: string[][]) => periods.some(([start, end]) => start <= day && day < end);
