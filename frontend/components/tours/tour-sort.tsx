"use client";

import { useTranslations } from "next-intl";
import { useId, useTransition } from "react";

import { useRouter } from "@/i18n/navigation";
import { pageHref } from "@/lib/pagination";

import { selectClass } from "./tour-filters";

const SORTS = ["next_departure", "base_price", "-base_price", "duration_days"] as const;

/** Tri des circuits ; les filtres en cours sont conservés, on revient à la page 1. */
export function TourSort({ pathname, query }: { pathname: string; query: Record<string, string | undefined> }) {
  const t = useTranslations("Tours");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const id = useId();

  return (
    <div className="flex items-center gap-2">
      <label htmlFor={id} className="shrink-0 text-sm font-semibold text-ocean-900">
        {t("sortLabel")}
      </label>
      <select
        id={id}
        value={query.ordering ?? "next_departure"}
        disabled={pending}
        className={selectClass}
        onChange={(event) => {
          const ordering = event.currentTarget.value === "next_departure" ? undefined : event.currentTarget.value;
          startTransition(() => router.push(pageHref(pathname, { ...query, ordering }, 1), { scroll: false }));
        }}
      >
        {SORTS.map((sort) => (
          <option key={sort} value={sort}>
            {t(`sort.${sort}`)}
          </option>
        ))}
      </select>
    </div>
  );
}
