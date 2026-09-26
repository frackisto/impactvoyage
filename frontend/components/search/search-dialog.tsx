"use client";

import { ArrowRightIcon, LoaderCircleIcon, SearchIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState, type FormEvent } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { MIN_QUERY_LENGTH, useGlobalSearch } from "@/hooks/use-global-search";
import { Link, useRouter } from "@/i18n/navigation";
import { searchHref } from "@/lib/search";
import { cn } from "@/lib/utils";

import { SearchResults } from "./search-results";

/**
 * Recherche instantanée de l'en-tête : résultats pendant la frappe, Entrée
 * ouvre la page de résultats complète (/recherche).
 */
export function SearchDialog({ label }: { label: string }) {
  const t = useTranslations("GlobalSearch");
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputId = useId();
  const statusId = useId();
  const { data, isFetching, isError } = useGlobalSearch(open ? query : "");
  const ready = query.trim().length >= MIN_QUERY_LENGTH;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;
    setOpen(false);
    router.push(searchHref(query));
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger aria-label={label} className={buttonVariants({ variant: "ghost", size: "icon" })}>
        <SearchIcon aria-hidden="true" className="size-5" />
      </DialogTrigger>
      <DialogContent
        closeLabel={t("close")}
        className="top-4 translate-y-0 gap-3 p-3 sm:top-24 sm:max-w-2xl sm:p-4"
      >
        <DialogTitle className="sr-only">{t("dialogTitle")}</DialogTitle>
        <form role="search" onSubmit={submit} className="flex items-center gap-2 pe-9">
          <label htmlFor={inputId} className="sr-only">
            {t("inputLabel")}
          </label>
          <SearchIcon aria-hidden="true" className="size-5 shrink-0 text-ocean-600" />
          <input
            id={inputId}
            type="search"
            autoFocus
            autoComplete="off"
            maxLength={100}
            value={query}
            onChange={(event) => setQuery(event.currentTarget.value)}
            placeholder={t("placeholder")}
            aria-describedby={statusId}
            // Pas de croix d'effacement native : elle se confondrait avec « Fermer ».
            className="h-11 min-w-0 flex-1 bg-transparent text-base text-ocean-950 outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:appearance-none"
          />
          {isFetching && <LoaderCircleIcon aria-hidden="true" className="size-5 animate-spin text-ocean-600" />}
          <Button type="submit" size="sm" disabled={!query.trim()}>
            {t("submit")}
          </Button>
        </form>

        <div className="max-h-[60vh] overflow-y-auto border-t pt-2">
          <p id={statusId} role="status" aria-live="polite" className={cn("px-2 py-1 text-sm text-muted-foreground", ready && data?.count ? "sr-only" : "")}>
            {!ready
              ? t("hint")
              : isError
                ? t("error")
                : data
                  ? t("found", { count: data.count })
                  : ""}
          </p>
          {ready && data && data.results.length > 0 && (
            <>
              <SearchResults results={data.results} compact onNavigate={() => setOpen(false)} />
              <Link
                href={searchHref(query)}
                onClick={() => setOpen(false)}
                className="mt-2 flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-semibold text-ocean-700 hover:bg-ocean-50"
              >
                {t("seeAll", { count: data.count, query: query.trim() })}
                <ArrowRightIcon aria-hidden="true" className="size-4 rtl:rotate-180" />
              </Link>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
