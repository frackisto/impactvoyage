/** Paragraphes d'un texte saisi dans l'admin (séparés par une ligne vide). */
export function paragraphs(text: string | null | undefined): string[] {
  return (text ?? "").split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
}

/** Résumé pour les balises description / Open Graph (160 caractères au plus). */
export function excerpt(text: string, max = 160): string {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > max ? `${clean.slice(0, max - 1).trimEnd()}…` : clean;
}
