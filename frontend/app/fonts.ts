import { Dancing_Script, Fredoka, Nunito } from "next/font/google";

/**
 * Typographies inspirées du logo :
 * - Fredoka : titres, arrondis et chaleureux comme « Impact Voyage » ;
 * - Nunito : texte courant, très lisible ;
 * - Dancing Script : slogan manuscrit (« Voyagez, Rêvez, Explorez. »).
 */
export const displayFont = Fredoka({
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

export const bodyFont = Nunito({
  subsets: ["latin", "latin-ext"],
  variable: "--font-body",
  display: "swap",
});

export const sloganFont = Dancing_Script({
  subsets: ["latin", "latin-ext"],
  weight: ["600"],
  variable: "--font-slogan",
  display: "swap",
});
