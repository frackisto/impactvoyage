import { StarIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { formatRating } from "@/lib/format";
import { cn } from "@/lib/utils";

type RatingProps = { value: number | null | undefined; count?: number; className?: string };

/** Note sur 5 étoiles, lisible par les lecteurs d'écran (« Note : 4,5 sur 5 »). */
export function Rating({ value, count, className }: RatingProps) {
  const t = useTranslations("Rating");
  const locale = useLocale();
  if (value == null) return null;
  const rounded = Math.round(value * 2) / 2;

  return (
    <span className={cn("inline-flex items-center gap-1.5 text-sm", className)}>
      <span className="flex" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((star) => (
          <StarIcon
            key={star}
            className={cn(
              "size-4",
              star <= rounded ? "fill-sunset-500 text-sunset-500" : "fill-muted text-border",
            )}
          />
        ))}
      </span>
      <span className="sr-only">{t("label", { value: formatRating(value, locale) })}</span>
      <span aria-hidden="true" className="font-semibold text-ocean-900">
        {formatRating(value, locale)}
      </span>
      {count !== undefined && (
        <span className="text-muted-foreground">({t("count", { count })})</span>
      )}
    </span>
  );
}
