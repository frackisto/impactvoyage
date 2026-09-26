"use client";

import { useId, useTransition } from "react";

import { useRouter } from "@/i18n/navigation";
import { pageHref } from "@/lib/pagination";

import { selectClass } from "./filter-panel";

type SortSelectProps = {
  pathname: string;
  /** Filtres en cours, conservés ; on revient à la page 1. */
  query: Record<string, string | undefined>;
  label: string;
  /** La première option est le tri par défaut (absent de l'URL). */
  options: { value: string; label: string }[];
};

/** Tri d'une liste, dans le paramètre d'URL « ordering ». */
export function SortSelect({ pathname, query, label, options }: SortSelectProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const id = useId();
  const fallback = options[0]?.value;

  return (
    <div className="flex items-center gap-2">
      <label htmlFor={id} className="shrink-0 text-sm font-semibold text-ocean-900">
        {label}
      </label>
      <select
        id={id}
        value={query.ordering ?? fallback}
        disabled={pending}
        className={selectClass}
        onChange={(event) => {
          const ordering = event.currentTarget.value === fallback ? undefined : event.currentTarget.value;
          startTransition(() => router.push(pageHref(pathname, { ...query, ordering }, 1), { scroll: false }));
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
