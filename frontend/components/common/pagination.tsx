import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { pageHref, pageNumbers } from "@/lib/pagination";
import { cn } from "@/lib/utils";

type PaginationProps = {
  page: number;
  count: number;
  pageSize: number;
  /** Chemin de la liste, sans langue (« /destinations »). */
  pathname: string;
  /** Filtres en cours, conservés d'une page à l'autre. */
  query?: Record<string, string | undefined>;
};

/** Pagination par liens (indexable, fonctionne sans JavaScript). */
export function Pagination({ page, count, pageSize, pathname, query = {} }: PaginationProps) {
  const t = useTranslations("Pagination");
  const total = Math.ceil(count / pageSize);
  if (total <= 1) return null;
  const href = (p: number) => pageHref(pathname, query, p);
  const step = "size-10 px-0";

  return (
    <nav aria-label={t("label")} className="flex justify-center">
      <ul className="flex flex-wrap items-center gap-1">
        {page > 1 && (
          <li>
            <Link href={href(page - 1)} rel="prev" className={cn(buttonVariants({ variant: "outline" }), step)}>
              <ChevronLeftIcon aria-hidden="true" className="rtl:rotate-180" />
              <span className="sr-only">{t("previous")}</span>
            </Link>
          </li>
        )}
        {pageNumbers(page, total).map((p, i) =>
          p === "gap" ? (
            <li key={`gap-${i}`} aria-hidden="true" className="px-2 text-muted-foreground">
              …
            </li>
          ) : (
            <li key={p}>
              <Link
                href={href(p)}
                aria-current={p === page ? "page" : undefined}
                aria-label={t("page", { page: p })}
                className={cn(buttonVariants({ variant: p === page ? "default" : "ghost" }), step)}
              >
                {p}
              </Link>
            </li>
          ),
        )}
        {page < total && (
          <li>
            <Link href={href(page + 1)} rel="next" className={cn(buttonVariants({ variant: "outline" }), step)}>
              <ChevronRightIcon aria-hidden="true" className="rtl:rotate-180" />
              <span className="sr-only">{t("next")}</span>
            </Link>
          </li>
        )}
      </ul>
    </nav>
  );
}
