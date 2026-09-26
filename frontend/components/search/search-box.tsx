"use client";

import { SearchIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useTransition, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { useRouter } from "@/i18n/navigation";
import { searchHref } from "@/lib/search";

/** Champ de la page de résultats ; une nouvelle recherche repart de tous les types. */
export function SearchBox({ query }: { query: string }) {
  const t = useTranslations("GlobalSearch");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const id = useId();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = String(new FormData(event.currentTarget).get("q") ?? "").trim();
    if (value) startTransition(() => router.push(searchHref(value)));
  }

  return (
    <form
      role="search"
      onSubmit={submit}
      aria-busy={pending}
      className="flex w-full max-w-3xl items-center gap-2 rounded-2xl bg-white p-2 shadow-xl shadow-ocean-950/20"
    >
      <label htmlFor={id} className="sr-only">
        {t("inputLabel")}
      </label>
      <SearchIcon aria-hidden="true" className="ms-2 size-5 shrink-0 text-ocean-600" />
      <input
        id={id}
        name="q"
        type="search"
        defaultValue={query}
        key={query}
        maxLength={100}
        autoComplete="off"
        placeholder={t("placeholder")}
        className="h-11 min-w-0 flex-1 bg-transparent text-base text-ocean-950 outline-none placeholder:text-muted-foreground"
      />
      <Button type="submit" variant="cta" size="lg" disabled={pending}>
        {t("submit")}
      </Button>
    </form>
  );
}
