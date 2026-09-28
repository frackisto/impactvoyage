import { cn } from "@/lib/utils";

type Block = { type: "h2" | "p"; text: string } | { type: "ul"; items: string[] };

/**
 * Découpe un texte structuré en blocs : paragraphes séparés par une ligne
 * vide, « ## » pour un intertitre, « - » en début de ligne pour une liste.
 */
export function textBlocks(text: string | null | undefined): Block[] {
  return (text ?? "")
    .split(/\n\s*\n/)
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((chunk): Block => {
      if (chunk.startsWith("## ")) return { type: "h2", text: chunk.slice(3).trim() };
      const lines = chunk.split("\n").map((line) => line.trim());
      if (lines.every((line) => line.startsWith("- "))) return { type: "ul", items: lines.map((line) => line.slice(2).trim()) };
      return { type: "p", text: chunk };
    });
}

/**
 * Texte d'article (blog, pages légales) rendu sans HTML : aucun balisage saisi
 * n'est interprété, le contenu ne peut pas injecter de script.
 */
export function RichText({ text, className }: { text: string | null | undefined; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-5 text-lg leading-relaxed text-ocean-950/90", className)}>
      {textBlocks(text).map((block, index) =>
        block.type === "h2" ? (
          <h2 key={index} className="pt-3 text-2xl font-bold text-ocean-900">
            {block.text}
          </h2>
        ) : block.type === "ul" ? (
          <ul key={index} className="flex list-disc flex-col gap-2 ps-6 marker:text-sunset-600">
            {block.items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        ) : (
          <p key={index} className="whitespace-pre-line">
            {block.text}
          </p>
        ),
      )}
    </div>
  );
}
