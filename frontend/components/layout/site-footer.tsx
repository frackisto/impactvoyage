import { ClockIcon, MailIcon, MapPinIcon, PhoneIcon } from "lucide-react";
import Image from "next/image";
import { getTranslations } from "next-intl/server";

import { Container } from "@/components/common/container";
import { SocialIcon } from "@/components/common/social-icons";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { LEGAL_NAV, MAIN_NAV } from "@/lib/navigation";
import { getSiteSettings, socialLinks, whatsappUrl } from "@/services/site.service";

const EXPLORE = ["destinations", "tours", "accommodations", "vehicles", "offers", "events"];
const AGENCY = ["services", "media", "about", "contact"];

/** Pied de page complet (CdC § 4, § 19) : agence, navigation, coordonnées, réseaux, mentions. */
export async function SiteFooter() {
  const [t, settings] = await Promise.all([getTranslations(), getSiteSettings()]);
  const socials = socialLinks(settings);
  const whatsapp = whatsappUrl(settings.whatsapp);
  const navItem = (key: string) => MAIN_NAV.find((item) => item.key === key);

  return (
    <footer className="bg-ocean-950 text-ocean-100">
      <Container className="grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <span className="rounded-2xl bg-white p-1.5">
              <Image src="/brand/emblem.png" alt="" width={48} height={48} className="size-12" />
            </span>
            <span className="font-heading text-lg font-bold leading-tight text-white">{t("Brand.name")}</span>
          </div>
          <p className="font-script text-2xl text-sunset-400">{t("Brand.slogan")}</p>
          <p className="text-sm">{t("Footer.pitch")}</p>
          {socials.length > 0 && (
            <ul className="flex gap-2" aria-label={t("Footer.social")}>
              {socials.map(([network, url]) => (
                <li key={network}>
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={network}
                    className="flex size-10 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-sunset-500 hover:text-ocean-950"
                  >
                    <SocialIcon network={network} className="size-5" />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>

        {[
          { title: t("Footer.explore"), keys: EXPLORE },
          { title: t("Footer.agency"), keys: AGENCY },
        ].map((column) => (
          <nav key={column.title} aria-label={column.title}>
            <h2 className="mb-4 font-heading text-lg font-semibold text-white">{column.title}</h2>
            <ul className="flex flex-col gap-2.5 text-sm">
              {column.keys.map((key) => {
                const item = navItem(key);
                return item ? (
                  <li key={key}>
                    <Link href={item.href} className="hover:text-sunset-400 hover:underline">
                      {t(`Nav.${key}`)}
                    </Link>
                  </li>
                ) : null;
              })}
            </ul>
          </nav>
        ))}

        <div>
          <h2 className="mb-4 font-heading text-lg font-semibold text-white">{t("Footer.contactUs")}</h2>
          <ul className="flex flex-col gap-3 text-sm">
            {settings.address && (
              <li className="flex gap-2">
                <MapPinIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sunset-400" />
                <span>{settings.address}</span>
              </li>
            )}
            {settings.phone && (
              <li className="flex gap-2">
                <PhoneIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sunset-400" />
                <a href={`tel:${settings.phone.replace(/\s/g, "")}`} className="hover:text-white">{settings.phone}</a>
              </li>
            )}
            {whatsapp && (
              <li className="flex gap-2">
                <SocialIcon network="whatsapp" className="mt-0.5 size-4 shrink-0 text-sunset-400" />
                <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="hover:text-white">
                  WhatsApp {settings.whatsapp}
                </a>
              </li>
            )}
            {settings.email && (
              <li className="flex gap-2">
                <MailIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sunset-400" />
                <a href={`mailto:${settings.email}`} className="break-all hover:text-white">{settings.email}</a>
              </li>
            )}
            {settings.opening_hours && (
              <li className="flex gap-2">
                <ClockIcon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-sunset-400" />
                <span className="whitespace-pre-line">{settings.opening_hours}</span>
              </li>
            )}
          </ul>
          <Link href="/devis" className={`${buttonVariants({ variant: "cta" })} mt-5`}>
            {t("Nav.quote")}
          </Link>
        </div>
      </Container>

      <div className="border-t border-white/10">
        <Container className="flex flex-col items-center justify-between gap-3 py-5 text-sm sm:flex-row">
          <p>
            © {new Date().getFullYear()} {t("Brand.name")} SARLP. {t("Footer.rights")}
          </p>
          <ul className="flex flex-wrap justify-center gap-x-5 gap-y-2">
            {LEGAL_NAV.map((item) => (
              <li key={item.key}>
                <Link href={item.href} className="hover:text-white hover:underline">
                  {t(`Footer.${item.key}`)}
                </Link>
              </li>
            ))}
          </ul>
        </Container>
      </div>
    </footer>
  );
}
