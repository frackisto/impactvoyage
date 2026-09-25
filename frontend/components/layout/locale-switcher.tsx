"use client";

import { useLocale, useTranslations } from "next-intl";

import { Link, usePathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { cn } from "@/lib/utils";

/** Bascule FR/EN en restant sur la même page. */
export function LocaleSwitcher({ tone = "light" }: { tone?: "light" | "dark" }) {
  const locale = useLocale();
  const pathname = usePathname();
  const t = useTranslations("Nav");

  return (
    <nav
      aria-label={t("language")}
      className={cn("flex items-center rounded-lg border p-0.5 text-sm", tone === "dark" && "border-white/30")}
    >
      {routing.locales.map((code) => (
        <Link
          key={code}
          href={pathname}
          locale={code}
          hrefLang={code}
          aria-current={code === locale ? "true" : undefined}
          className={cn(
            // Cible d'au moins 32 × 32 px (WCAG 2.5.8 : 24 px minimum).
            "inline-flex min-h-8 min-w-8 items-center justify-center rounded-md px-2 font-semibold uppercase transition-colors",
            code === locale
              ? "bg-ocean-600 text-white"
              : tone === "dark"
                ? "text-ocean-100 hover:text-white"
                : "text-muted-foreground hover:text-foreground",
          )}
        >
          {code}
        </Link>
      ))}
    </nav>
  );
}
