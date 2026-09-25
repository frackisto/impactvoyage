"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useId, useTransition } from "react";

import { cn } from "@/lib/utils";

export const CURRENCIES = ["XOF", "EUR", "USD", "GBP"] as const;
const COOKIE = "iv_currency";

type CurrencySwitcherProps = {
  /** Devise courante, lue côté serveur (cookie) pour un rendu identique serveur/navigateur. */
  value: string;
  className?: string;
  tone?: "light" | "dark";
};

/**
 * Devise d'affichage (CdC § 36) : les prix restent en FCFA, la conversion est
 * indicative. Le choix est mémorisé dans un cookie lu par le serveur.
 */
export function CurrencySwitcher({ value, className, tone = "light" }: CurrencySwitcherProps) {
  const t = useTranslations("Currency");
  const router = useRouter();
  const id = useId();
  const [pending, startTransition] = useTransition();

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <label htmlFor={id} className="sr-only">
        {t("label")}
      </label>
      <select
        id={id}
        defaultValue={value}
        disabled={pending}
        onChange={(event) => {
          document.cookie = `${COOKIE}=${event.target.value}; path=/; max-age=31536000; samesite=lax`;
          startTransition(() => router.refresh());
        }}
        className={cn(
          "h-8 cursor-pointer rounded-md border bg-transparent px-2 text-sm font-medium",
          tone === "dark" ? "border-white/30 text-white [&>option]:text-ocean-950" : "border-border text-foreground",
        )}
      >
        {CURRENCIES.map((code) => (
          <option key={code} value={code}>
            {t(code)}
          </option>
        ))}
      </select>
    </div>
  );
}
