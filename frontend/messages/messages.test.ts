import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";

import en from "./en.json";
import fr from "./fr.json";

type Tree = { [key: string]: string | Tree };

function keys(tree: Tree, prefix = ""): string[] {
  return Object.entries(tree).flatMap(([key, value]) =>
    typeof value === "string" ? [`${prefix}${key}`] : keys(value, `${prefix}${key}.`),
  );
}

// Valeurs factices pour tous les paramètres utilisés dans les messages.
const VALUES = {
  count: 2, value: "4,5", date: "1 janv.", name: "Dubaï", title: "Circuit", min: 1, max: 4, number: 1,
  formatted: "3", index: 1, total: 3, alt: "Photo", country: "France", continent: "Europe", page: 2, year: 2026,
  rooms: 2, nights: 3, room: "Double", start: "1 nov.", end: "3 nov.", category: "SUV", seats: 5, day: "samedi 10 octobre",
};

describe("messages", () => {
  it("FR et EN ont exactement les mêmes clés", () => {
    expect(keys(en as Tree).sort()).toEqual(keys(fr as Tree).sort());
  });

  for (const [locale, messages] of Object.entries({ fr, en })) {
    it(`${locale} : tous les messages sont valides (syntaxe ICU)`, () => {
      const errors: string[] = [];
      const t = createTranslator({
        locale,
        messages,
        onError: (error) => errors.push(error.message),
        getMessageFallback: ({ key }) => key,
      });
      for (const key of keys(messages as Tree)) {
        // @ts-expect-error clé dynamique : on parcourt tout le dictionnaire.
        t(key, VALUES);
      }
      expect(errors).toEqual([]);
    });
  }
});
