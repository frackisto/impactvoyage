import { BedDoubleIcon, UsersIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { Price } from "@/components/common/price";
import { Rating } from "@/components/common/rating";
import { pageHref } from "@/lib/pagination";
import type { HotelList, Schemas } from "@/types";

import { Stars } from "./stars";

/** Carte complète (liste) ou réduite (hébergements d'une destination). */
export type HotelCardData = Schemas["HotelCard"] &
  Partial<Pick<HotelList, "destination" | "price_from" | "rating_avg" | "rating_count">>;

export type ResidenceCardData = Schemas["ResidenceCard"] & Partial<Pick<Schemas["ResidenceList"], "destination">>;

type StayQuery = Record<string, string | undefined>;

/**
 * Carte d'un hôtel : type, étoiles, destination, note, prix « à partir de » par nuit.
 * `stay` (dates, voyageurs, chambres) est transmis à la fiche pour afficher les disponibilités.
 */
export function HotelCard({ hotel, stay = {}, priority, showDestination = true }: {
  hotel: HotelCardData;
  stay?: StayQuery;
  priority?: boolean;
  showDestination?: boolean;
}) {
  const t = useTranslations("Stays");
  const showType = Boolean(hotel.accommodation_type && hotel.accommodation_type !== "HOTEL");
  return (
    <ContentCard
      href={pageHref(`/hotels/${hotel.slug}`, stay, 1)}
      title={hotel.name}
      eyebrow={showDestination ? hotel.destination?.name : undefined}
      description={hotel.short_description}
      image={hotel.cover_image}
      imageAlt={hotel.cover_alt || hotel.name}
      priority={priority}
      // Catégorie (étoiles) sur la photo, note des avis sous le texte : deux notions distinctes.
      badges={
        (showType || hotel.stars) && (
          <>
            {showType && (
              <span className="rounded-4xl bg-white/95 px-2.5 py-0.5 text-xs font-semibold text-ocean-900">
                {t(`type.${hotel.accommodation_type}`)}
              </span>
            )}
            {hotel.stars ? (
              <span className="inline-flex rounded-4xl bg-white/95 px-2 py-1">
                <Stars count={hotel.stars} className="[&_svg]:size-3.5" />
              </span>
            ) : null}
          </>
        )
      }
      meta={hotel.rating_count ? <Rating value={hotel.rating_avg} count={hotel.rating_count} /> : undefined}
      footer={hotel.price_from ? <Price value={hotel.price_from} from unit="night" /> : undefined}
    />
  );
}

/** Carte d'une résidence meublée : chambres, capacité, prix par nuit. */
export function ResidenceCard({ residence, stay = {}, priority, showDestination = true }: {
  residence: ResidenceCardData;
  stay?: StayQuery;
  priority?: boolean;
  showDestination?: boolean;
}) {
  const t = useTranslations("Stays");
  return (
    <ContentCard
      href={pageHref(`/residences/${residence.slug}`, stay, 1)}
      title={residence.name}
      eyebrow={showDestination ? residence.destination?.name : undefined}
      description={residence.short_description}
      image={residence.cover_image}
      imageAlt={residence.cover_alt || residence.name}
      priority={priority}
      meta={
        <>
          <span className="inline-flex items-center gap-1">
            <BedDoubleIcon aria-hidden="true" className="size-4" /> {t("bedrooms", { count: residence.rooms_count })}
          </span>
          <span className="inline-flex items-center gap-1">
            <UsersIcon aria-hidden="true" className="size-4" /> {t("guests", { count: residence.capacity })}
          </span>
        </>
      }
      footer={<Price value={residence.price_per_night} from unit="night" />}
    />
  );
}
