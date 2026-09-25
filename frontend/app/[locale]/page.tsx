import Image from "next/image";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

/** Accueil provisoire aux couleurs du logo ; la vraie page d'accueil arrive en Phase 10. */
export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-ocean-50 to-background">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 px-4 py-20 text-center">
        <Image
          src="/brand/logo.png"
          alt={t("Brand.logoAlt")}
          width={180}
          height={180}
          priority
          className="size-44"
        />
        <h1 className="text-balance text-4xl font-bold text-ocean-800 sm:text-5xl">
          {t("Home.heroTitle")}
        </h1>
        <p className="font-script text-3xl text-sunset-600">{t("Brand.slogan")}</p>
        <p className="max-w-2xl text-lg text-muted-foreground">{t("Home.heroSubtitle")}</p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/destinations" className={cn(buttonVariants({ size: "lg" }), "h-11 px-6 text-base")}>
            {t("Home.discover")}
          </Link>
          <Link
            href="/devis"
            className={cn(
              buttonVariants({ size: "lg" }),
              "h-11 bg-cta px-6 text-base text-cta-foreground hover:bg-sunset-400",
            )}
          >
            {t("Nav.quote")}
          </Link>
        </div>
        <p className="text-sm text-muted-foreground">{t("Home.comingSoon")}</p>
      </div>
    </section>
  );
}
