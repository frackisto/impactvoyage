import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";

export type OfferBadgeCode = "NOUVEAU" | "PROMOTION" | "POPULAIRE" | "DERNIERES_PLACES";

const VARIANT = {
  NOUVEAU: "nouveau",
  PROMOTION: "promotion",
  POPULAIRE: "populaire",
  DERNIERES_PLACES: "dernieres_places",
} as const;

/** Badge d'offre (CdC § 17) : Nouveau, Promotion, Populaire, Dernières places. */
export function OfferBadge({ code, className }: { code: OfferBadgeCode | "" | null | undefined; className?: string }) {
  const t = useTranslations("OfferBadge");
  if (!code) return null;
  return (
    <Badge variant={VARIANT[code]} className={className}>
      {t(code)}
    </Badge>
  );
}
