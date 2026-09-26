import { StarIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";

/** Catégorie d'un hôtel (1 à 5 étoiles), lisible par les lecteurs d'écran. */
export function Stars({ count, className }: { count?: number | null; className?: string }) {
  const t = useTranslations("Stays");
  if (!count) return null;
  return (
    <span className={cn("inline-flex items-center", className)}>
      <span className="sr-only">{t("stars", { count })}</span>
      {Array.from({ length: count }, (_, i) => (
        <StarIcon key={i} aria-hidden="true" className="size-4 fill-sunset-500 text-sunset-500" />
      ))}
    </span>
  );
}
