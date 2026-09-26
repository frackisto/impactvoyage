import { MapPinIcon } from "lucide-react";
import Image from "next/image";

import { Breadcrumbs, type Crumb } from "@/components/common/breadcrumbs";
import { Container } from "@/components/common/container";
import { Rating } from "@/components/common/rating";
import { mediaSrc } from "@/lib/media";
import type { DestinationDetail } from "@/types";

type DestinationHeroProps = {
  destination: DestinationDetail;
  /** « 🇦🇪 Émirats arabes unis » */
  country: string;
  continent: string;
  breadcrumbs: Crumb[];
};

/** En-tête immersif d'une destination : grande photo, nom, pays, accroche et note. */
export function DestinationHero({ destination, country, continent, breadcrumbs }: DestinationHeroProps) {
  const image = mediaSrc(destination.cover_image);
  const { rating } = destination;
  const place = [destination.city !== destination.name && destination.city, country].filter(Boolean).join(", ");

  return (
    <section className="relative isolate overflow-hidden bg-ocean-950 text-white">
      {image && (
        <Image
          src={image}
          alt={destination.cover_alt || destination.name}
          fill
          priority
          sizes="100vw"
          className="-z-10 object-cover opacity-75"
        />
      )}
      <div aria-hidden="true" className="absolute inset-0 -z-10 bg-gradient-to-t from-ocean-950 via-ocean-950/50 to-ocean-950/30" />
      <Container className="flex min-h-[26rem] flex-col justify-between gap-10 py-8 sm:min-h-[32rem] sm:py-10">
        <Breadcrumbs items={breadcrumbs} />
        <div className="flex max-w-3xl flex-col gap-4">
          <p className="inline-flex w-fit items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm font-semibold backdrop-blur-sm">
            <MapPinIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {place} · {continent}
          </p>
          <h1 className="text-balance text-4xl font-bold drop-shadow-sm sm:text-6xl">{destination.name}</h1>
          {destination.short_description && (
            <p className="text-pretty text-lg text-ocean-50 sm:text-xl">{destination.short_description}</p>
          )}
          {rating.count > 0 && (
            <Rating value={rating.average} count={rating.count} inverse />
          )}
        </div>
      </Container>
    </section>
  );
}
