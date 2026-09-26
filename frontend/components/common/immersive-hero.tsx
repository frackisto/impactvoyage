import Image from "next/image";

import { mediaSrc } from "@/lib/media";
import type { RatingSummary } from "@/types";

import { Breadcrumbs, type Crumb } from "./breadcrumbs";
import { Container } from "./container";
import { Rating } from "./rating";

type ImmersiveHeroProps = {
  image?: string | null;
  imageAlt: string;
  breadcrumbs: Crumb[];
  /** Pastille au-dessus du titre (lieu, type de circuit...). */
  badge?: React.ReactNode;
  title: string;
  subtitle?: string;
  rating?: RatingSummary;
  /** Informations clés sous le sous-titre (durée, thème...). */
  children?: React.ReactNode;
};

/** En-tête des fiches (destination, circuit...) : grande photo, fil d'Ariane, titre et note. */
export function ImmersiveHero({ image, imageAlt, breadcrumbs, badge, title, subtitle, rating, children }: ImmersiveHeroProps) {
  const src = mediaSrc(image);

  return (
    <section className="relative isolate overflow-hidden bg-ocean-950 text-white">
      {src && <Image src={src} alt={imageAlt} fill priority sizes="100vw" className="-z-10 object-cover opacity-75" />}
      <div aria-hidden="true" className="absolute inset-0 -z-10 bg-gradient-to-t from-ocean-950 via-ocean-950/50 to-ocean-950/30" />
      <Container className="flex min-h-[26rem] flex-col justify-between gap-10 py-8 sm:min-h-[32rem] sm:py-10">
        <Breadcrumbs items={breadcrumbs} />
        <div className="flex max-w-3xl flex-col gap-4">
          {badge && (
            <p className="inline-flex w-fit items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm font-semibold backdrop-blur-sm">
              {badge}
            </p>
          )}
          <h1 className="text-balance text-4xl font-bold drop-shadow-sm sm:text-6xl">{title}</h1>
          {subtitle && <p className="text-pretty text-lg text-ocean-50 sm:text-xl">{subtitle}</p>}
          {rating && rating.count > 0 && <Rating value={rating.average} count={rating.count} inverse />}
          {children}
        </div>
      </Container>
    </section>
  );
}
