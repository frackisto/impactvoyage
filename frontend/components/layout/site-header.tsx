import { MailIcon, PhoneIcon, SearchIcon } from "lucide-react";
import Image from "next/image";
import { cookies } from "next/headers";
import { getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { SocialIcon } from "@/components/common/social-icons";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { CURRENCY_COOKIE } from "@/lib/api/server";
import { cn } from "@/lib/utils";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";

import { AccountLink } from "./account-link";
import { CurrencySwitcher } from "./currency-switcher";
import { DesktopNav } from "./desktop-nav";
import { LocaleSwitcher } from "./locale-switcher";
import { MobileNav } from "./mobile-nav";

/**
 * En-tête collant (CdC § 4, § 5) :
 * - barre supérieure (grand écran) : coordonnées, langue, devise, compte ;
 * - barre principale : logo, menu, recherche globale, « Demander un devis ».
 */
export async function SiteHeader() {
  const [t, settings, store] = await Promise.all([getTranslations(), getSiteSettings(), cookies()]);
  const currency = store.get(CURRENCY_COOKIE)?.value ?? "XOF";
  const whatsapp = whatsappUrl(settings.whatsapp);

  return (
    <header className="sticky top-0 z-40">
      <div className="hidden bg-ocean-950 text-ocean-50 lg:block">
        <Container className="flex h-10 items-center justify-between gap-6 text-sm">
          <ul className="flex items-center gap-5">
            {settings.phone && (
              <li>
                <a href={`tel:${settings.phone.replace(/\s/g, "")}`} className="inline-flex items-center gap-1.5 hover:text-sunset-400">
                  <PhoneIcon aria-hidden="true" className="size-4" /> {settings.phone}
                </a>
              </li>
            )}
            {settings.email && (
              <li>
                <a href={`mailto:${settings.email}`} className="inline-flex items-center gap-1.5 hover:text-sunset-400">
                  <MailIcon aria-hidden="true" className="size-4" /> {settings.email}
                </a>
              </li>
            )}
            {whatsapp && (
              <li>
                <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 hover:text-sunset-400">
                  <SocialIcon network="whatsapp" className="size-4" /> WhatsApp
                </a>
              </li>
            )}
          </ul>
          <div className="flex items-center gap-4">
            <AccountLink className="text-ocean-50" />
            <CurrencySwitcher value={currency} tone="dark" />
            <LocaleSwitcher tone="dark" />
          </div>
        </Container>
      </div>

      <div className="border-b bg-background/95 shadow-sm backdrop-blur supports-backdrop-filter:bg-background/85">
        <Container className="flex h-18 items-center justify-between gap-4">
          <Link href="/" className="flex shrink-0 items-center gap-2.5" aria-label={t("Nav.homeLink")}>
            <Image src="/brand/emblem.png" alt="" width={52} height={52} priority className="size-12 sm:size-13" />
            <span className="flex flex-col leading-none">
              <span className="font-heading text-lg font-bold text-ocean-600 sm:text-xl">Impact Voyage</span>
              <span className="font-heading text-xs font-semibold tracking-wide text-ocean-800">
                {t("Brand.tagline")}
              </span>
            </span>
          </Link>

          <DesktopNav />

          <div className="flex items-center gap-1 sm:gap-2">
            <Link
              href="/recherche"
              aria-label={t("Header.search")}
              className={buttonVariants({ variant: "ghost", size: "icon" })}
            >
              <SearchIcon aria-hidden="true" className="size-5" />
            </Link>
            <Link href="/devis" className={cn(buttonVariants({ variant: "cta" }), "hidden sm:inline-flex")}>
              {t("Nav.quote")}
            </Link>
            <MobileNav phone={settings.phone} email={settings.email} currency={currency} />
          </div>
        </Container>
      </div>
    </header>
  );
}
