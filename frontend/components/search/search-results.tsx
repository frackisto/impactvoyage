import {
  BusFrontIcon,
  CalendarDaysIcon,
  CarIcon,
  HotelIcon,
  HouseIcon,
  MapIcon,
  MapPinIcon,
  TicketIcon,
  type LucideIcon,
} from "lucide-react";
import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";

import { Price } from "@/components/common/price";
import { Link } from "@/i18n/navigation";
import { countryFlag, countryName } from "@/lib/countries";
import { mediaSrc } from "@/lib/media";
import { resultHref, type SearchType } from "@/lib/search";
import { cn } from "@/lib/utils";
import type { SearchResult } from "@/types";

export const TYPE_ICONS: Record<SearchType, LucideIcon> = {
  destination: MapPinIcon,
  tour: MapIcon,
  hotel: HotelIcon,
  residence: HouseIcon,
  vehicle: CarIcon,
  activity: TicketIcon,
  event: CalendarDaysIcon,
};

type SearchResultsProps = {
  results: SearchResult[];
  /** Version réduite (recherche instantanée de l'en-tête). */
  compact?: boolean;
  onNavigate?: () => void;
};

/** Résultats de la recherche globale, tous types confondus (CdC § 7). */
export function SearchResults({ results, compact, onNavigate }: SearchResultsProps) {
  const t = useTranslations("GlobalSearch");
  const locale = useLocale();

  return (
    <ul className={cn("flex flex-col", compact ? "gap-1" : "gap-4")}>
      {results.map((result) => {
        const Icon = TYPE_ICONS[result.type] ?? BusFrontIcon;
        const image = mediaSrc(result.image);
        // Destination : le contexte est le code pays (« AE ») → « 🇦🇪 Émirats arabes unis ».
        const context =
          result.type === "destination" && /^[A-Z]{2}$/.test(result.context)
            ? `${countryFlag(result.context)} ${countryName(result.context, locale)}`
            : result.context;
        return (
          <li key={`${result.type}-${result.slug}`}>
            <Link
              href={resultHref(result)}
              onClick={onNavigate}
              className={cn(
                "group flex items-center gap-4 rounded-2xl transition-colors focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
                compact ? "p-2 hover:bg-ocean-50" : "border bg-card p-3 hover:border-ocean-300 hover:shadow-md sm:p-4",
              )}
            >
              <span
                className={cn(
                  "relative flex shrink-0 items-center justify-center overflow-hidden rounded-xl bg-ocean-50 text-ocean-400",
                  compact ? "size-12" : "size-20 sm:h-24 sm:w-32",
                )}
              >
                {image ? (
                  <Image src={image} alt="" fill sizes={compact ? "48px" : "128px"} className="object-cover" />
                ) : (
                  <Icon aria-hidden="true" className={compact ? "size-5" : "size-8"} />
                )}
              </span>
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-sunset-700">
                  <Icon aria-hidden="true" className="size-3.5" />
                  {t(`type.${result.type}`)}
                  {context && <span className="truncate font-medium normal-case tracking-normal text-muted-foreground">· {context}</span>}
                </span>
                <span className={cn("font-semibold text-ocean-950 group-hover:text-ocean-700", compact ? "truncate" : "text-lg")}>
                  {result.title}
                </span>
                {!compact && result.excerpt && <span className="line-clamp-2 text-sm text-muted-foreground">{result.excerpt}</span>}
              </span>
              {!compact && result.price && result.price_unit && (
                <Price value={result.price} from unit={result.price_unit} compact className="hidden shrink-0 text-end sm:inline-flex" />
              )}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
