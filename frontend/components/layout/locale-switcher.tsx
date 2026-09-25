"use client";

import { useLocale, useTranslations } from "next-intl";

import { Link, usePathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { cn } from "@/lib/utils";

/** Bascule FR/EN en restant sur la même page. */
export function LocaleSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();
  const t = useTranslations("Nav");

  return (
    <nav aria-label={t("language")} className="flex items-center rounded-lg border p-0.5 text-sm">
      {routing.locales.map((code) => (
        <Link
          key={code}
          href={pathname}
          locale={code}
          hrefLang={code}
          aria-current={code === locale ? "true" : undefined}
          className={cn(
            "rounded-md px-2 py-1 font-semibold uppercase transition-colors",
            code === locale ? "bg-ocean-600 text-white" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {code}
        </Link>
      ))}
    </nav>
  );
}
