import { ChevronRightIcon } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export type Crumb = { label: string; href?: string };

/** Fil d'Ariane (précédé de « Accueil ») sur fond sombre ; la dernière étape est la page courante. */
export async function Breadcrumbs({ items }: { items: Crumb[] }) {
  const t = await getTranslations("Nav");
  const crumbs: Crumb[] = [{ label: t("home"), href: "/" }, ...items];

  return (
    <nav aria-label={t("breadcrumb")}>
      <ol className="flex flex-wrap items-center gap-1 text-sm text-ocean-100">
        {crumbs.map((crumb, index) => (
          <li key={crumb.label} className="flex items-center gap-1">
            {index > 0 && <ChevronRightIcon aria-hidden="true" className="size-4 rtl:rotate-180" />}
            {crumb.href && index < crumbs.length - 1 ? (
              <Link href={crumb.href} className="hover:text-white hover:underline">
                {crumb.label}
              </Link>
            ) : (
              <span aria-current={index === crumbs.length - 1 ? "page" : undefined}>{crumb.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
