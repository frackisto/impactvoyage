import type { Crumb } from "@/components/common/breadcrumbs";
import { absoluteUrl } from "@/lib/seo";

/**
 * Données structurées Schema.org. « < » est échappé : un texte saisi dans
 * l'admin ne peut pas fermer la balise script.
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}

/** BreadcrumbList à partir du fil d'Ariane affiché (les étapes sans lien pointent vers la page courante). */
export function breadcrumbList(crumbs: Crumb[], currentHref: string, locale: string) {
  return {
    "@type": "BreadcrumbList",
    itemListElement: crumbs.map((crumb, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: crumb.label,
      item: absoluteUrl(crumb.href ?? currentHref, locale),
    })),
  };
}
