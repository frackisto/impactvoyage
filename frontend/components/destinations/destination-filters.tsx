"use client";

import { SearchIcon, XIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useId, useTransition, type FormEvent } from "react";

import { pageHref } from "@/lib/pagination";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useRouter } from "@/i18n/navigation";
import { countryFlag, countryName } from "@/lib/countries";
import { cn } from "@/lib/utils";

export type FilterValues = { continent?: string; country?: string; search?: string };

type DestinationFiltersProps = {
  /** Continents réellement proposés, avec leur nombre de destinations. */
  continents: { value: string; count: number }[];
  /** Pays proposés et leur continent (le choix est limité au continent sélectionné). */
  countries: { code: string; continent: string }[];
  current: FilterValues;
};

const PATH = "/destinations";

const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm";

/**
 * Filtres de la liste des destinations (CdC § 8) : continents en un clic,
 * pays et recherche par nom. Les filtres vivent dans l'URL (partageable,
 * indexable) ; la page est rendue côté serveur.
 */
export function DestinationFilters({ continents, countries, current }: DestinationFiltersProps) {
  const t = useTranslations("Destinations");
  const locale = useLocale();
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const countryId = useId();
  const searchId = useId();

  const choices = countries
    .filter((c) => !current.continent || c.continent === current.continent)
    .map((c) => ({ code: c.code, name: countryName(c.code, locale) }))
    .sort((a, b) => a.name.localeCompare(b.name, locale));

  function navigate(values: FilterValues) {
    startTransition(() => router.push(pageHref(PATH, values, 1), { scroll: false }));
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    navigate({
      continent: current.continent,
      country: String(data.get("country") ?? "") || undefined,
      search: String(data.get("search") ?? "").trim() || undefined,
    });
  }

  const hasFilters = Boolean(current.continent || current.country || current.search);
  const chip = (active: boolean) =>
    cn(
      "inline-flex h-10 items-center gap-2 rounded-full border px-4 text-sm font-semibold transition-colors",
      active
        ? "border-ocean-600 bg-ocean-600 text-white"
        : "border-ocean-200 bg-background text-ocean-900 hover:border-ocean-400 hover:bg-ocean-50",
    );

  return (
    <div className="flex flex-col gap-5" aria-busy={pending}>
      <nav aria-label={t("continentsLabel")}>
        <ul className="flex flex-wrap gap-2">
          <li>
            <Link
              href={pageHref(PATH, { search: current.search }, 1)}
              scroll={false}
              aria-current={!current.continent ? "true" : undefined}
              className={chip(!current.continent)}
            >
              {t("allContinents")}
            </Link>
          </li>
          {continents.map(({ value, count }) => (
            <li key={value}>
              <Link
                href={pageHref(PATH, { continent: value, search: current.search }, 1)}
                scroll={false}
                aria-current={current.continent === value ? "true" : undefined}
                className={chip(current.continent === value)}
              >
                {t(`continent.${value}`)}
                <span className="text-xs font-medium opacity-80">{count}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <form
        onSubmit={submit}
        role="search"
        aria-label={t("filtersLabel")}
        // key : le formulaire reprend les valeurs de l'URL après chaque navigation.
        key={`${current.continent}-${current.country}-${current.search}`}
        className="grid items-end gap-4 sm:grid-cols-[1fr_1fr_auto]"
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor={searchId} className="text-sm font-semibold text-ocean-900">
            {t("searchLabel")}
          </label>
          <Input
            id={searchId}
            name="search"
            type="search"
            defaultValue={current.search}
            placeholder={t("searchPlaceholder")}
            maxLength={100}
            autoComplete="off"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={countryId} className="text-sm font-semibold text-ocean-900">
            {t("country")}
          </label>
          <select
            id={countryId}
            name="country"
            defaultValue={current.country ?? ""}
            className={selectClass}
            onChange={(event) => event.currentTarget.form?.requestSubmit()}
          >
            <option value="">{t("allCountries")}</option>
            {choices.map((c) => (
              <option key={c.code} value={c.code}>
                {countryFlag(c.code)} {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button type="submit" size="lg" disabled={pending}>
            <SearchIcon aria-hidden="true" data-icon="inline-start" />
            {t("apply")}
          </Button>
          {hasFilters && (
            <Link href={PATH} scroll={false} className={buttonVariants({ variant: "ghost", size: "lg" })}>
              <XIcon aria-hidden="true" data-icon="inline-start" />
              {t("reset")}
            </Link>
          )}
        </div>
      </form>
    </div>
  );
}
