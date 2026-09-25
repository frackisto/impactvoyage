import Image from "next/image";
import { getTranslations } from "next-intl/server";

import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

import { LocaleSwitcher } from "./locale-switcher";

/**
 * En-tête provisoire (logo, langue, appel à l'action). La navigation complète
 * du CdC § 5 et le menu mobile arrivent avec le design system (Phase 9).
 */
export async function SiteHeader() {
  const t = await getTranslations();
  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4">
        <Link href="/" className="flex items-center gap-2" aria-label={t("Brand.name")}>
          <Image
            src="/brand/logo.png"
            alt={t("Brand.logoAlt")}
            width={48}
            height={48}
            priority
            className="size-12"
          />
          <span className="hidden font-heading text-lg font-bold text-ocean-600 sm:inline">
            Impact Voyage
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <LocaleSwitcher />
          <Link href="/devis" className={cn(buttonVariants({ size: "lg" }), "bg-cta text-cta-foreground hover:bg-sunset-400")}>
            {t("Nav.quote")}
          </Link>
        </div>
      </div>
    </header>
  );
}
