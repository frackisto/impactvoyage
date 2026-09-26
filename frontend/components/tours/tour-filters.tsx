"use client";

import { SlidersHorizontalIcon, XIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState, useTransition, type FormEvent, type ReactNode } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useRouter } from "@/i18n/navigation";
import { pageHref } from "@/lib/pagination";
import { cn } from "@/lib/utils";

export type TourFilterValues = Record<
  "destination" | "theme" | "departure_from" | "departure_to" | "max_days" | "travelers" | "max_price" | "ordering",
  string | undefined
>;

type TourFiltersProps = {
  /** Chemin de la liste (/circuits/nationaux ou /circuits/internationaux). */
  pathname: string;
  destinations: { slug: string; name: string }[];
  themes: { slug: string; name: string }[];
  current: TourFilterValues;
};

const DURATIONS = [1, 2, 3, 5, 7, 10, 15];

export const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm";

function Field({ label, children }: { label: string; children: (id: string) => ReactNode }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-ocean-900">
        {label}
      </label>
      {children(id)}
    </div>
  );
}

/**
 * Filtres des circuits (CdC § 7, § 10) : les noms des champs sont ceux de l'API
 * et du moteur de recherche de l'accueil. Repliés sur mobile, en colonne sur
 * grand écran ; les listes déroulantes s'appliquent dès qu'on les change.
 */
export function TourFilters({ pathname, destinations, themes, current }: TourFiltersProps) {
  const t = useTranslations("Tours");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const today = new Date().toISOString().slice(0, 10);

  const active = Object.entries(current).filter(([key, value]) => key !== "ordering" && value).length;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values: Record<string, string | undefined> = { ordering: current.ordering };
    new FormData(event.currentTarget).forEach((value, key) => {
      if (typeof value === "string" && value.trim()) values[key] = value.trim();
    });
    startTransition(() => router.push(pageHref(pathname, values, 1), { scroll: false }));
  }

  const autoSubmit = (event: React.ChangeEvent<HTMLSelectElement>) => event.currentTarget.form?.requestSubmit();

  return (
    <div className="flex flex-col gap-3" aria-busy={pending}>
      <Button
        type="button"
        variant="outline"
        size="lg"
        className="w-full justify-between lg:hidden"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="inline-flex items-center gap-2">
          <SlidersHorizontalIcon aria-hidden="true" />
          {t("filters")}
        </span>
        {active > 0 && <span className="rounded-full bg-ocean-600 px-2 text-xs text-white">{active}</span>}
      </Button>

      <form
        id={panelId}
        onSubmit={submit}
        role="search"
        aria-label={t("filtersLabel")}
        // key : le formulaire reprend les valeurs de l'URL après chaque navigation.
        key={JSON.stringify(current)}
        className={cn("flex-col gap-4 rounded-2xl border bg-card p-5", open ? "flex" : "hidden lg:flex")}
      >
        <h2 className="hidden text-lg font-bold text-ocean-900 lg:block">{t("filters")}</h2>
        {destinations.length > 0 && (
          <Field label={t("destination")}>
            {(id) => (
              <select id={id} name="destination" defaultValue={current.destination ?? ""} className={selectClass} onChange={autoSubmit}>
                <option value="">{t("anyDestination")}</option>
                {destinations.map((d) => (
                  <option key={d.slug} value={d.slug}>
                    {d.name}
                  </option>
                ))}
              </select>
            )}
          </Field>
        )}
        {themes.length > 0 && (
          <Field label={t("theme")}>
            {(id) => (
              <select id={id} name="theme" defaultValue={current.theme ?? ""} className={selectClass} onChange={autoSubmit}>
                <option value="">{t("anyTheme")}</option>
                {themes.map((theme) => (
                  <option key={theme.slug} value={theme.slug}>
                    {theme.name}
                  </option>
                ))}
              </select>
            )}
          </Field>
        )}
        <Field label={t("departureFrom")}>
          {(id) => <Input id={id} name="departure_from" type="date" min={today} defaultValue={current.departure_from} />}
        </Field>
        <Field label={t("departureTo")}>
          {(id) => <Input id={id} name="departure_to" type="date" min={today} defaultValue={current.departure_to} />}
        </Field>
        <Field label={t("maxDays")}>
          {(id) => (
            <select id={id} name="max_days" defaultValue={current.max_days ?? ""} className={selectClass} onChange={autoSubmit}>
              <option value="">{t("anyDuration")}</option>
              {DURATIONS.map((days) => (
                <option key={days} value={days}>
                  {t("upToDays", { count: days })}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label={t("travelers")}>
          {(id) => (
            <Input id={id} name="travelers" type="number" min={1} max={99} inputMode="numeric" defaultValue={current.travelers} />
          )}
        </Field>
        <Field label={t("maxPrice")}>
          {(id) => (
            <Input id={id} name="max_price" type="number" min={0} step={5000} inputMode="numeric" defaultValue={current.max_price} />
          )}
        </Field>
        <div className="flex flex-col gap-2 pt-1">
          <Button type="submit" size="lg" disabled={pending}>
            {t("apply")}
          </Button>
          {active > 0 && (
            <Link
              href={pageHref(pathname, { ordering: current.ordering }, 1)}
              scroll={false}
              className={buttonVariants({ variant: "ghost" })}
            >
              <XIcon aria-hidden="true" data-icon="inline-start" />
              {t("reset")}
            </Link>
          )}
        </div>
      </form>
    </div>
  );
}
