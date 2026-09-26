import { ClockIcon, StarIcon, UsersIcon } from "lucide-react";
import { getLocale, getTranslations } from "next-intl/server";

import { ContentCard } from "@/components/common/content-card";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { intlLocale } from "@/lib/format";
import type { DestinationDetail } from "@/types";

const grid = "grid gap-6 sm:grid-cols-2 lg:grid-cols-3";

/**
 * « Circuits, hôtels, résidences et activités disponibles » (CdC § 8) :
 * une section par type d'offre publiée ; rien n'est affiché pour un type vide.
 */
export async function DestinationOffers({ destination }: { destination: DestinationDetail }) {
  const [t, tSearch, locale] = await Promise.all([getTranslations("Destinations"), getTranslations("Search"), getLocale()]);
  const { tours, hotels, residences, activities } = destination;
  const hours = (value: string) =>
    t("hours", { count: Number(value), formatted: new Intl.NumberFormat(intlLocale(locale)).format(Number(value)) });

  return (
    <>
      {tours.length > 0 && (
        <Section tone="tint" aria-labelledby="destination-tours">
          <SectionHeader id="destination-tours" eyebrow={t("bookEyebrow")} title={t("toursTitle")} />
          <div className={grid}>
            {tours.map((tour) => (
              <ContentCard
                key={tour.id}
                href={`/circuits/${tour.slug}`}
                title={tour.title}
                description={tour.short_description}
                image={tour.cover_image}
                imageAlt={tour.cover_alt || tour.title}
                meta={
                  <span className="inline-flex items-center gap-1">
                    <ClockIcon aria-hidden="true" className="size-4" /> {tSearch("days", { count: tour.duration_days })}
                  </span>
                }
                footer={<Price value={tour.price} from unit="person" />}
              />
            ))}
          </div>
        </Section>
      )}

      {hotels.length > 0 && (
        <Section aria-labelledby="destination-hotels">
          <SectionHeader id="destination-hotels" eyebrow={t("stayEyebrow")} title={t("hotelsTitle")} />
          <div className={grid}>
            {hotels.map((hotel) => (
              <ContentCard
                key={hotel.id}
                href={`/hotels/${hotel.slug}`}
                title={hotel.name}
                description={hotel.short_description}
                image={hotel.cover_image}
                imageAlt={hotel.cover_alt || hotel.name}
                meta={
                  hotel.stars ? (
                    <span className="inline-flex items-center gap-1">
                      <StarIcon aria-hidden="true" className="size-4 fill-sunset-500 text-sunset-500" />
                      {tSearch("stars", { count: hotel.stars })}
                    </span>
                  ) : undefined
                }
              />
            ))}
          </div>
        </Section>
      )}

      {residences.length > 0 && (
        <Section tone={hotels.length > 0 ? "tint" : "light"} aria-labelledby="destination-residences">
          <SectionHeader id="destination-residences" eyebrow={t("stayEyebrow")} title={t("residencesTitle")} />
          <div className={grid}>
            {residences.map((residence) => (
              <ContentCard
                key={residence.id}
                href={`/residences/${residence.slug}`}
                title={residence.name}
                description={residence.short_description}
                image={residence.cover_image}
                imageAlt={residence.cover_alt || residence.name}
                meta={
                  <span className="inline-flex items-center gap-1">
                    <UsersIcon aria-hidden="true" className="size-4" /> {t("capacity", { count: residence.capacity })}
                  </span>
                }
                footer={<Price value={residence.price_per_night} from unit="night" />}
              />
            ))}
          </div>
        </Section>
      )}

      {activities.length > 0 && (
        <Section aria-labelledby="destination-activities">
          <SectionHeader id="destination-activities" eyebrow={t("doEyebrow")} title={t("activitiesTitle")} />
          <div className={grid}>
            {activities.map((activity) => (
              <ContentCard
                key={activity.id}
                href={`/activites/${activity.slug}`}
                title={activity.title}
                description={activity.short_description}
                image={activity.cover_image}
                imageAlt={activity.cover_alt || activity.title}
                meta={
                  <span className="inline-flex items-center gap-1">
                    <ClockIcon aria-hidden="true" className="size-4" /> {hours(activity.duration_hours)}
                  </span>
                }
                footer={<Price value={activity.price} from unit="person" />}
              />
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

/** Vrai si la destination a au moins une offre publiée. */
export function hasOffers({ tours, hotels, residences, activities }: DestinationDetail) {
  return tours.length + hotels.length + residences.length + activities.length > 0;
}
