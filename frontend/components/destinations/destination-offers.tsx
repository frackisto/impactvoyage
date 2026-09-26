import { getTranslations } from "next-intl/server";

import { HotelCard, ResidenceCard } from "@/components/accommodations/stay-cards";
import { ActivityCard } from "@/components/activities/activity-card";
import { Section, SectionHeader } from "@/components/common/page-section";
import { TourCard } from "@/components/tours/tour-card";
import type { DestinationDetail } from "@/types";

const grid = "grid gap-6 sm:grid-cols-2 lg:grid-cols-3";

/**
 * « Circuits, hôtels, résidences et activités disponibles » (CdC § 8) :
 * une section par type d'offre publiée ; rien n'est affiché pour un type vide.
 */
export async function DestinationOffers({ destination }: { destination: DestinationDetail }) {
  const t = await getTranslations("Destinations");
  const { tours, hotels, residences, activities } = destination;

  return (
    <>
      {tours.length > 0 && (
        <Section tone="tint" aria-labelledby="destination-tours">
          <SectionHeader id="destination-tours" eyebrow={t("bookEyebrow")} title={t("toursTitle")} />
          <div className={grid}>
            {tours.map((tour) => (
              <TourCard key={tour.id} tour={tour} showDestination={false} />
            ))}
          </div>
        </Section>
      )}

      {hotels.length > 0 && (
        <Section aria-labelledby="destination-hotels">
          <SectionHeader id="destination-hotels" eyebrow={t("stayEyebrow")} title={t("hotelsTitle")} />
          <div className={grid}>
            {hotels.map((hotel) => (
              <HotelCard key={hotel.id} hotel={hotel} showDestination={false} />
            ))}
          </div>
        </Section>
      )}

      {residences.length > 0 && (
        <Section tone={hotels.length > 0 ? "tint" : "light"} aria-labelledby="destination-residences">
          <SectionHeader id="destination-residences" eyebrow={t("stayEyebrow")} title={t("residencesTitle")} />
          <div className={grid}>
            {residences.map((residence) => (
              <ResidenceCard key={residence.id} residence={residence} showDestination={false} />
            ))}
          </div>
        </Section>
      )}

      {activities.length > 0 && (
        <Section aria-labelledby="destination-activities">
          <SectionHeader id="destination-activities" eyebrow={t("doEyebrow")} title={t("activitiesTitle")} />
          <div className={grid}>
            {activities.map((activity) => (
              <ActivityCard key={activity.id} activity={activity} showDestination={false} />
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
