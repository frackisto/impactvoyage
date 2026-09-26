import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/common/breadcrumbs";
import { Container } from "@/components/common/container";
import { EmptyState, ErrorState } from "@/components/common/states";
import { SearchBox } from "@/components/search/search-box";
import { SearchResults, TYPE_ICONS } from "@/components/search/search-results";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { MAIN_NAV } from "@/lib/navigation";
import { SEARCH_TYPES, searchHref, type SearchType } from "@/lib/search";
import { param } from "@/lib/search-params";
import { cn } from "@/lib/utils";
import { globalSearch } from "@/services/search.service";
import type { SearchResponse } from "@/types";

type Props = PageProps<"/[locale]/recherche">;

function parse(query: Record<string, string | string[] | undefined>) {
  const q = param(query, "q")?.slice(0, 100) ?? "";
  const type = param(query, "type");
  return { q, type: SEARCH_TYPES.includes(type as SearchType) ? (type as SearchType) : undefined };
}

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "GlobalSearch" });
  const { q } = parse(query);
  return {
    title: q ? t("metaTitleQuery", { query: q }) : t("title"),
    // Les pages de résultats ne sont jamais indexées.
    robots: { index: false, follow: true },
  };
}

/** Recherche globale (CdC § 7) : tous les contenus publiés, par type. */
export default async function SearchPage({ params, searchParams }: Props) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const [t, tNav] = await Promise.all([getTranslations("GlobalSearch"), getTranslations("Nav")]);
  const { q, type } = parse(query);

  let all: SearchResponse | null = null;
  let filtered: SearchResponse | null = null;
  let failed = false;
  if (q) {
    try {
      // Compteurs de tous les types pour les onglets ; résultats du type choisi.
      [all, filtered] = await Promise.all([globalSearch(q), type ? globalSearch(q, type) : Promise.resolve(null)]);
    } catch {
      failed = true;
    }
  }
  const shown = type ? filtered : all;
  const suggestions = MAIN_NAV.filter((item) => ["destinations", "tours", "accommodations", "vehicles", "events"].includes(item.key));

  return (
    <>
      <section className="bg-gradient-to-br from-ocean-800 to-ocean-950 text-white">
        <Container className="flex flex-col gap-5 py-10 sm:py-14">
          <Breadcrumbs items={[{ label: t("title") }]} />
          <h1 className="text-balance text-3xl font-bold sm:text-5xl">
            {q ? t("resultsFor", { query: q }) : t("title")}
          </h1>
          <SearchBox query={q} />
        </Container>
      </section>

      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {!q ? (
          <EmptyState
            title={t("startTitle")}
            description={t("startText")}
            action={<SuggestionLinks items={suggestions} label={(key) => tNav(key)} />}
          />
        ) : failed ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : all && all.count > 0 ? (
          <>
            <nav aria-label={t("typesLabel")}>
              <ul className="flex flex-wrap gap-2">
                <li>
                  <TypeTab href={searchHref(q)} active={!type} label={t("all")} count={all.count} />
                </li>
                {SEARCH_TYPES.filter((key) => all.counts[key]).map((key) => {
                  const Icon = TYPE_ICONS[key];
                  return (
                    <li key={key}>
                      <TypeTab
                        href={searchHref(q, key)}
                        active={type === key}
                        label={t(`types.${key}`)}
                        count={all.counts[key]}
                        icon={<Icon aria-hidden="true" className="size-4" />}
                      />
                    </li>
                  );
                })}
              </ul>
            </nav>
            <section aria-labelledby="search-results" className="flex flex-col gap-4">
              <h2 id="search-results" className="text-lg font-semibold text-ocean-900">
                {t("found", { count: shown?.count ?? 0 })}
              </h2>
              {shown && shown.results.length > 0 ? (
                <SearchResults results={shown.results} />
              ) : (
                <EmptyState title={t("emptyTypeTitle")} description={t("emptyTypeText")} />
              )}
              {shown && shown.count > shown.results.length && (
                <p className="text-sm text-muted-foreground">{t("refine", { shown: shown.results.length, count: shown.count })}</p>
              )}
            </section>
          </>
        ) : (
          <EmptyState
            title={t("noneTitle", { query: q })}
            description={t("noneText")}
            action={
              <div className="flex flex-col items-center gap-4">
                <SuggestionLinks items={suggestions} label={(key) => tNav(key)} />
                <Link href="/devis" className={buttonVariants({ variant: "cta" })}>
                  {t("askAgency")}
                </Link>
              </div>
            }
          />
        )}
      </Container>
    </>
  );
}

function TypeTab({ href, active, label, count, icon }: { href: string; active: boolean; label: string; count: number; icon?: React.ReactNode }) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "inline-flex h-10 items-center gap-2 rounded-full border px-4 text-sm font-semibold transition-colors",
        active ? "border-ocean-600 bg-ocean-600 text-white" : "border-ocean-200 bg-background text-ocean-900 hover:bg-ocean-50",
      )}
    >
      {icon}
      {label}
      <span className={cn("text-xs font-medium", active ? "text-ocean-100" : "text-muted-foreground")}>{count}</span>
    </Link>
  );
}

function SuggestionLinks({ items, label }: { items: { key: string; href: string }[]; label: (key: string) => string }) {
  return (
    <ul className="flex flex-wrap justify-center gap-2">
      {items.map((item) => (
        <li key={item.key}>
          <Link href={item.href} className={buttonVariants({ variant: "outline" })}>
            {label(item.key)}
          </Link>
        </li>
      ))}
    </ul>
  );
}
