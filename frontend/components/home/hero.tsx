import Image from "next/image";
import { getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { mediaSrc } from "@/lib/media";
import type { SiteSettings } from "@/types";

/**
 * Hero de l'accueil (CdC § 6) : grande photo (choisie dans les paramètres du
 * site), slogan, sous-titre et deux appels à l'action. Le voile sombre garantit
 * la lisibilité du texte blanc quelle que soit la photo.
 */
export async function Hero({ settings, children }: { settings: Partial<SiteSettings>; children?: React.ReactNode }) {
  const t = await getTranslations();
  const image = mediaSrc(settings.hero_image) ?? "/brand/emblem.png";

  return (
    <section className="relative isolate">
      <div className="absolute inset-0 -z-10 overflow-hidden bg-ocean-950">
        <Image
          src={image}
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-ocean-950/70 via-ocean-950/40 to-ocean-950/80" />
      </div>
      <Container className="flex min-h-[34rem] flex-col items-center justify-center gap-5 pb-40 pt-20 text-center text-white sm:min-h-[38rem]">
        <p className="font-script text-3xl text-sunset-300 sm:text-4xl">
          {settings.slogan || t("Brand.slogan")}
        </p>
        <h1 className="max-w-4xl text-balance text-4xl font-bold leading-tight drop-shadow-sm sm:text-6xl">
          {t("Home.heroTitle")}
        </h1>
        <p className="max-w-2xl text-pretty text-lg text-ocean-50 sm:text-xl">
          {settings.hero_subtitle || t("Home.heroSubtitle")}
        </p>
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <Link href="/destinations" className={buttonVariants({ variant: "inverse", size: "lg" })}>
            {t("Home.discover")}
          </Link>
          <Link href="/devis" className={buttonVariants({ variant: "cta", size: "lg" })}>
            {t("Nav.quote")}
          </Link>
        </div>
      </Container>
      {children && <Container className="relative z-10 -mt-32 pb-4">{children}</Container>}
    </section>
  );
}
