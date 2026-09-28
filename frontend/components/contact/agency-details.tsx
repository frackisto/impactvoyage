import { ClockIcon, ExternalLinkIcon, MailIcon, MapPinIcon, PhoneIcon } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { SocialIcon } from "@/components/common/social-icons";
import { SITE_URL } from "@/lib/seo";
import { whatsappUrl } from "@/services/site.service";
import type { SiteSettings } from "@/types";

/** Coordonnées de l'agence (CdC § 19), saisies dans l'administration. */
export async function AgencyDetails({ settings }: { settings: Partial<SiteSettings> }) {
  const t = await getTranslations("Contact");
  const whatsapp = whatsappUrl(settings.whatsapp);
  const mapUrl = settings.address
    ? settings.latitude && settings.longitude
      ? `https://www.openstreetmap.org/?mlat=${settings.latitude}&mlon=${settings.longitude}#map=17/${settings.latitude}/${settings.longitude}`
      : `https://www.openstreetmap.org/search?query=${encodeURIComponent(settings.address)}`
    : null;
  const row = "flex gap-3";
  const icon = "mt-0.5 size-5 shrink-0 text-sunset-600";

  return (
    <ul className="flex flex-col gap-4 text-ocean-950">
      {settings.address && (
        <li className={row}>
          <MapPinIcon aria-hidden="true" className={icon} />
          <span className="flex flex-col gap-1">
            <span className="sr-only">{t("address")} :</span>
            <span>{settings.address}</span>
            {mapUrl && (
              <a href={mapUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm font-semibold text-ocean-700 hover:underline">
                {t("seeMap")}
                <ExternalLinkIcon aria-hidden="true" className="size-3.5" />
                <span className="sr-only">{t("newTab")}</span>
              </a>
            )}
          </span>
        </li>
      )}
      {settings.phone && (
        <li className={row}>
          <PhoneIcon aria-hidden="true" className={icon} />
          <a href={`tel:${settings.phone.replace(/\s/g, "")}`} className="font-semibold hover:underline">
            <span className="sr-only">{t("phone")} : </span>
            {settings.phone}
          </a>
        </li>
      )}
      {whatsapp && (
        <li className={row}>
          <SocialIcon network="whatsapp" className={icon} />
          <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="font-semibold hover:underline">
            <span className="sr-only">WhatsApp : </span>
            {settings.whatsapp}
            <span className="sr-only"> {t("newTab")}</span>
          </a>
        </li>
      )}
      {settings.email && (
        <li className={row}>
          <MailIcon aria-hidden="true" className={icon} />
          <a href={`mailto:${settings.email}`} className="font-semibold break-all hover:underline">
            <span className="sr-only">{t("email")} : </span>
            {settings.email}
          </a>
        </li>
      )}
      {settings.opening_hours && (
        <li className={row}>
          <ClockIcon aria-hidden="true" className={icon} />
          <span className="flex flex-col">
            <span className="font-semibold">{t("hours")}</span>
            <span className="whitespace-pre-line text-sm">{settings.opening_hours}</span>
          </span>
        </li>
      )}
    </ul>
  );
}

/** Données structurées TravelAgency (fiche d'entreprise dans les moteurs de recherche). */
export function travelAgencyJsonLd(settings: Partial<SiteSettings>) {
  return {
    "@type": "TravelAgency",
    name: settings.agency_name,
    url: SITE_URL,
    telephone: settings.phone || undefined,
    email: settings.email || undefined,
    address: settings.address || undefined,
    geo:
      settings.latitude && settings.longitude
        ? { "@type": "GeoCoordinates", latitude: settings.latitude, longitude: settings.longitude }
        : undefined,
  };
}
