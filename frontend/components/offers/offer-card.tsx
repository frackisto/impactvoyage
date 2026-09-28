import { useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { OfferBadge, type OfferBadgeCode } from "@/components/common/offer-badge";
import { Price } from "@/components/common/price";
import type { OfferList } from "@/types";

/** Carte d'offre promotionnelle (CdC § 17) : badge, réduction, prix barré et prix promo. */
export function OfferCard({ offer, priority }: { offer: OfferList; priority?: boolean }) {
  const t = useTranslations("Offers");
  return (
    <ContentCard
      href={`/offres/${offer.slug}`}
      title={offer.title}
      eyebrow={t(`type.${offer.offer_type}`)}
      description={offer.short_description}
      image={offer.cover_image}
      imageAlt={offer.cover_alt || offer.title}
      priority={priority}
      badges={
        <>
          <OfferBadge code={offer.badge as OfferBadgeCode} />
          {offer.discount_percent > 0 && (
            <span className="rounded-4xl bg-white px-2 py-0.5 text-xs font-bold text-ocean-900">−{offer.discount_percent} %</span>
          )}
        </>
      }
      footer={
        <span className="flex flex-col">
          <Price value={offer.initial_price} strikethrough />
          <Price value={offer.promo_price} />
        </span>
      }
    />
  );
}
