import { CalendarDaysIcon, ClockIcon, MapPinIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { Price } from "@/components/common/price";
import { Rating } from "@/components/common/rating";
import { formatDate } from "@/lib/format";
import type { Schemas, TourList } from "@/types";

/** Carte complète (liste) ou réduite (circuits d'une destination, sans destination ni départ). */
export type TourCardData = Schemas["TourCard"] &
  Partial<Pick<TourList, "destination" | "theme" | "is_custom" | "next_departure" | "rating_avg" | "rating_count">>;

/** Carte d'un circuit : destination, durée, prochain départ, note et prix par personne. */
export function TourCard({ tour, priority, showDestination = true }: { tour: TourCardData; priority?: boolean; showDestination?: boolean }) {
  const t = useTranslations("Tours");
  const locale = useLocale();

  return (
    <ContentCard
      href={`/circuits/${tour.slug}`}
      title={tour.title}
      eyebrow={showDestination ? tour.destination?.name : undefined}
      description={tour.short_description}
      image={tour.cover_image}
      imageAlt={tour.cover_alt || tour.title}
      priority={priority}
      badges={
        (tour.theme || tour.is_custom) && (
          <>
            {tour.is_custom && (
              <span className="rounded-4xl bg-cta px-2.5 py-0.5 text-xs font-bold text-cta-foreground">{t("custom")}</span>
            )}
            {tour.theme && (
              <span className="rounded-4xl bg-white/95 px-2.5 py-0.5 text-xs font-semibold text-ocean-900">{tour.theme.name}</span>
            )}
          </>
        )
      }
      meta={
        <>
          <span className="inline-flex items-center gap-1">
            <ClockIcon aria-hidden="true" className="size-4" /> {t("days", { count: tour.duration_days })}
          </span>
          {tour.next_departure ? (
            <span className="inline-flex items-center gap-1">
              <CalendarDaysIcon aria-hidden="true" className="size-4" />
              {t("nextDeparture", { date: formatDate(tour.next_departure, locale, { day: "numeric", month: "short" }) })}
            </span>
          ) : tour.is_custom ? (
            <span className="inline-flex items-center gap-1">
              <MapPinIcon aria-hidden="true" className="size-4" /> {t("yourDates")}
            </span>
          ) : null}
          {tour.rating_count ? <Rating value={tour.rating_avg} count={tour.rating_count} /> : null}
        </>
      }
      footer={<Price value={tour.price} from unit="person" />}
    />
  );
}
