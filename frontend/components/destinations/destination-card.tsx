import { HotelIcon, MapIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { countryFlag, countryName } from "@/lib/countries";
import type { DestinationList } from "@/types";

/** Carte d'une destination : pays (drapeau), accroche, nombre de circuits et d'hôtels. */
export function DestinationCard({ destination, priority }: { destination: DestinationList; priority?: boolean }) {
  const t = useTranslations("Destinations");
  const locale = useLocale();
  const { tours_count: tours, hotels_count: hotels } = destination;

  return (
    <ContentCard
      href={`/destinations/${destination.slug}`}
      title={destination.name}
      eyebrow={`${countryFlag(destination.country_code)} ${countryName(destination.country_code, locale)}`}
      description={destination.short_description}
      image={destination.cover_image}
      imageAlt={destination.cover_alt || destination.name}
      priority={priority}
      meta={
        (tours > 0 || hotels > 0) && (
          <>
            {tours > 0 && (
              <span className="inline-flex items-center gap-1">
                <MapIcon aria-hidden="true" className="size-4" /> {t("toursCount", { count: tours })}
              </span>
            )}
            {hotels > 0 && (
              <span className="inline-flex items-center gap-1">
                <HotelIcon aria-hidden="true" className="size-4" /> {t("hotelsCount", { count: hotels })}
              </span>
            )}
          </>
        )
      }
    />
  );
}
