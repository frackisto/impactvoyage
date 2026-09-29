import { CalendarDaysIcon } from "lucide-react";
import { getLocale, getTranslations } from "next-intl/server";

import { Price } from "@/components/common/price";
import { SocialIcon } from "@/components/common/social-icons";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { TourDetail } from "@/types";

/** Seuil d'affichage « Plus que N places ». */
const FEW_SEATS = 5;

/** Demande de réservation d'un départ (/reservation?tour=…&departure=…). */
export function bookHref(tour: TourDetail, departureId: number) {
  return `/reservation?${new URLSearchParams({ tour: tour.slug, departure: String(departureId) })}`;
}

export function quoteHref(tour: TourDetail, departureId?: number) {
  const params = new URLSearchParams({ tour: tour.slug });
  if (departureId) params.set("departure", String(departureId));
  return `/devis?${params}`;
}

/**
 * Encadré de réservation d'un circuit : prix par personne (et promotion),
 * départs ouverts avec les places restantes et leur réservation en ligne,
 * demande de devis préremplie (voyage sur mesure, groupe...).
 */
export async function TourBookingCard({ tour, whatsapp }: { tour: TourDetail; whatsapp: string | null }) {
  const [t, locale] = await Promise.all([getTranslations("Tours"), getLocale()]);
  const date = (value: string) => formatDate(value, locale, { weekday: "short", day: "numeric", month: "short", year: "numeric" });

  return (
    <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
      <h2 id="tour-booking" className="text-xl font-bold text-ocean-900">
        {t("bookTitle")}
      </h2>
      {tour.promo_price ? (
        <div className="flex flex-col">
          <Price value={tour.price} strikethrough />
          <Price value={tour.promo_price} unit="person" />
        </div>
      ) : (
        <Price value={tour.price} from unit="person" />
      )}

      {tour.departures.length > 0 ? (
        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-sunset-700">{t("departures")}</h3>
          <ul className="flex flex-col gap-2">
            {tour.departures.map((departure) => {
              const few = departure.seats_left <= FEW_SEATS;
              const specialPrice = departure.price && departure.price.amount !== tour.price?.amount;
              return (
                <li key={departure.id} className="flex items-center justify-between gap-3 rounded-2xl border p-3">
                  <div className="flex min-w-0 flex-col gap-1">
                    <span className="inline-flex items-center gap-1.5 font-semibold text-ocean-950">
                      <CalendarDaysIcon aria-hidden="true" className="size-4 shrink-0 text-ocean-600" />
                      {date(departure.start_date)}
                    </span>
                    {departure.end_date !== departure.start_date && (
                      <span className="ps-5.5 text-sm text-muted-foreground">
                        {t("returnOn", { date: date(departure.end_date) })}
                      </span>
                    )}
                    <span className={cn("ps-5.5 text-sm font-medium", few ? "text-sunset-800" : "text-ocean-700")}>
                      {few ? t("fewSeats", { count: departure.seats_left }) : t("seats", { count: departure.seats_left })}
                    </span>
                    {specialPrice && <Price value={departure.price} compact className="ps-5.5" />}
                  </div>
                  <Link
                    href={bookHref(tour, departure.id)}
                    aria-label={t("chooseDeparture", { date: date(departure.start_date) })}
                    className={cn(buttonVariants({ variant: "cta" }), "shrink-0")}
                  >
                    {t("choose")}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ) : (
        <p className="rounded-2xl bg-ocean-50 p-4 text-sm text-ocean-900">{t("noDeparture")}</p>
      )}

      <div className="flex flex-col gap-2">
        <Link href={quoteHref(tour)} className={cn(buttonVariants({ variant: tour.departures.length > 0 ? "outline" : "cta", size: "lg" }), "w-full")}>
          {t("quote")}
        </Link>
        {whatsapp && (
          <a
            href={`${whatsapp}?text=${encodeURIComponent(t("whatsappMessage", { title: tour.title }))}`}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}
          >
            <SocialIcon network="whatsapp" className="size-5 text-[#128C7E]" />
            {t("whatsapp")}
          </a>
        )}
      </div>
    </div>
  );
}
