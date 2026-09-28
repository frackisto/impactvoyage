import { describe, expect, it } from "vitest";

import { textBlocks } from "./rich-text";

describe("textBlocks", () => {
  it("reconnaît intertitres, listes et paragraphes", () => {
    const text = "Introduction.\n\n## Titre\n\n- un\n- deux\n\nLigne 1\nligne 2\n\n\n";
    expect(textBlocks(text)).toEqual([
      { type: "p", text: "Introduction." },
      { type: "h2", text: "Titre" },
      { type: "ul", items: ["un", "deux"] },
      { type: "p", text: "Ligne 1\nligne 2" },
    ]);
  });

  it("n'interprète pas le HTML et accepte un texte vide", () => {
    expect(textBlocks("<script>x</script>")).toEqual([{ type: "p", text: "<script>x</script>" }]);
    expect(textBlocks(null)).toEqual([]);
  });
});
