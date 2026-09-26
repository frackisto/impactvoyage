import { useLocale, useTranslations } from "next-intl";

import { displayMoney } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Money } from "@/types";

type PriceProps = {
  value: Money | null | undefined;
  /** Unité affichée après le prix : par personne, par nuit, par jour. */
  unit?: "person" | "night" | "day";
  /** Affiche « À partir de ». */
  from?: boolean;
  /** Prix barré (prix initial d'une offre). */
  strikethrough?: boolean;
  /** Taille réduite (tableaux de tarifs). */
  compact?: boolean;
  className?: string;
};

/**
 * Prix dans la devise choisie par le visiteur. Une conversion est signalée
 * comme indicative, avec le prix d'origine en FCFA (seul contractuel).
 */
export function Price({ value, unit, from, strikethrough, compact, className }: PriceProps) {
  const t = useTranslations("Price");
  const locale = useLocale();
  if (!value) return null;
  const { text, original } = displayMoney(value, locale);

  if (strikethrough) {
    return (
      <span className={cn("text-sm text-muted-foreground line-through", className)}>
        <span className="sr-only">{t("initialPrice")} </span>
        {text}
      </span>
    );
  }
  return (
    <span className={cn("inline-flex flex-col", className)}>
      <span>
        {from && <span className="text-sm font-normal text-muted-foreground">{t("from")} </span>}
        <span className={cn("font-heading font-bold text-ocean-800", compact ? "text-base" : "text-xl")}>{text}</span>
        {unit && <span className="text-sm text-muted-foreground"> / {t(unit)}</span>}
      </span>
      {original && (
        <span className="text-xs text-muted-foreground" title={t("indicative")}>
          ≈ {t("indicative")} · {original}
        </span>
      )}
    </span>
  );
}
