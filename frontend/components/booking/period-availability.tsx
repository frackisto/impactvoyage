import { CheckCircle2Icon, XCircleIcon } from "lucide-react";
import { getLocale, getTranslations } from "next-intl/server";

import { Price } from "@/components/common/price";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate, multiplyMoney } from "@/lib/format";
import { nights } from "@/lib/stay";
import { cn } from "@/lib/utils";
import type { Availability, Money } from "@/types";

type PeriodAvailabilityProps = {
  /** Réponse de /availability/ ; null si la vérification a échoué. */
  availability: Availability | null;
  start: string;
  end: string;
  /** Prix unitaire (par nuit ou par jour) pour le total indicatif. */
  unitPrice: Money | null | undefined;
  unit: "night" | "day";
  /** Demande de réservation préremplie (/reservation?…). */
  bookHref: string;
  /** Demande de devis préremplie (/devis?…). */
  requestHref: string;
};

/**
 * Résultat d'une vérification de disponibilité sur une période : libre (avec le
 * total indicatif, la réservation et le devis préremplis) ou déjà réservé (avec les périodes).
 */
export async function PeriodAvailability({ availability, start, end, unitPrice, unit, bookHref, requestHref }: PeriodAvailabilityProps) {
  const [t, locale] = await Promise.all([getTranslations("Availability"), getLocale()]);
  const date = (value: string) => formatDate(value, locale, { day: "numeric", month: "long" });
  const count = nights(start, end);
  const total = count && unitPrice ? multiplyMoney(unitPrice, count) : null;

  if (!availability) {
    return (
      <p role="status" className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-800">
        {t("error")}
      </p>
    );
  }

  return (
    <div
      role="status"
      className={cn(
        "flex flex-col gap-3 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between",
        availability.available ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50",
      )}
    >
      <div className="flex flex-col gap-1">
        <p className={cn("inline-flex items-center gap-2 font-semibold", availability.available ? "text-emerald-800" : "text-rose-800")}>
          {availability.available ? (
            <CheckCircle2Icon aria-hidden="true" className="size-5 shrink-0" />
          ) : (
            <XCircleIcon aria-hidden="true" className="size-5 shrink-0" />
          )}
          {availability.available ? t("available", { start: date(start), end: date(end) }) : t("booked")}
        </p>
        {!availability.available && availability.booked_periods.length > 0 && (
          <p className="text-sm text-rose-800">
            {t("bookedPeriods")}{" "}
            {availability.booked_periods.map(([from, to]) => t("period", { start: date(from), end: date(to) })).join(", ")}
          </p>
        )}
        {availability.available && total && (
          <p className="text-sm text-emerald-900">
            {t(unit === "night" ? "totalNights" : "totalDays", { count })} <Price value={total} compact className="inline-flex" />
          </p>
        )}
      </div>
      {availability.available && (
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link href={bookHref} className={buttonVariants({ variant: "cta" })}>
            {t("book")}
          </Link>
          <Link href={requestHref} className={buttonVariants({ variant: "outline" })}>
            {t("request")}
          </Link>
        </div>
      )}
    </div>
  );
}
