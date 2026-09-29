import { CalendarDaysIcon, CheckCircle2Icon, CheckIcon, CircleIcon, LinkIcon, XIcon } from "lucide-react";
import type { Metadata } from "next";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { BookingCancel } from "@/components/booking/booking-cancel";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { EmptyState } from "@/components/common/states";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { param } from "@/lib/search-params";
import { addDays } from "@/lib/stay";
import { cn } from "@/lib/utils";
import { getClientBooking, type BookingKind } from "@/services/bookings.service";
import type { Booking } from "@/types";

type Props = PageProps<"/[locale]/reservation/[reference]">;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, reference } = await params;
  const t = await getTranslations({ locale, namespace: "BookingTracking" });
  // Page personnelle (lien secret) : jamais indexée.
  return { title: t("metaTitle", { reference }), robots: { index: false, follow: false } };
}

const STEPS = ["REQUESTED", "CONFIRMED", "COMPLETED"] as const;
type Status = NonNullable<Booking["status"]>;

/** Étapes franchies ; une demande refusée, annulée ou expirée s'arrête à la deuxième. */
function progress(status: Status) {
  if (status === "COMPLETED") return { reached: 3, stopped: false };
  if (status === "CONFIRMED") return { reached: 2, stopped: false };
  if (status === "REQUESTED" || status === "PENDING") return { reached: 1, stopped: false };
  return { reached: 1, stopped: true };
}

/** Fiche publique d'une ligne de réservation. */
const FICHE: Record<BookingKind, string> = {
  tour_departure: "/circuits",
  room: "/hotels",
  residence: "/residences",
  vehicle: "/vehicules",
  activity: "/activites",
};

/**
 * Suivi d'une réservation par le client (CdC § 12, § 13), sans compte : lien
 * reçu par email /reservation/{reference}?token=… Statut, prestations, total ;
 * annulation possible tant que l'agence n'a pas confirmé.
 */
export default async function BookingTrackingPage({ params, searchParams }: Props) {
  const [{ locale, reference }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("BookingTracking");
  const lang = await getLocale();
  const token = param(query, "token") ?? "";
  const booking = token ? await getClientBooking(reference, token).catch(() => null) : null;

  if (!booking) {
    return (
      <>
        <PageHeader title={t("invalidTitle")} breadcrumbs={[{ label: t("breadcrumb") }]} />
        <Container className="py-12">
          <EmptyState
            icon={LinkIcon}
            title={t("invalidTitle")}
            description={t("invalidText")}
            action={
              <Link href="/contact" className={buttonVariants({ variant: "cta" })}>
                {t("contactUs")}
              </Link>
            }
          />
        </Container>
      </>
    );
  }

  const status: Status = booking.status ?? "REQUESTED";
  const day = (value: string) => formatDate(`${value}T00:00:00Z`, lang, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const { reached, stopped } = progress(status);
  const justSent = param(query, "sent") === "1";

  return (
    <>
      <PageHeader
        title={t("title", { reference: booking.reference ?? reference })}
        description={t("hello", { name: booking.contact_name })}
        breadcrumbs={[{ label: t("breadcrumb") }]}
      />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-8">
          {justSent && (
            <div role="status" className="flex gap-4 rounded-3xl border border-emerald-200 bg-emerald-50 p-6">
              <CheckCircle2Icon aria-hidden="true" className="size-8 shrink-0 text-emerald-700" />
              <div className="flex flex-col gap-1">
                <p className="text-xl font-bold text-ocean-900">{t("sentTitle")}</p>
                <p className="text-ocean-950">{t("sentText", { email: booking.contact_email })}</p>
              </div>
            </div>
          )}

          <section aria-labelledby="booking-status" className="flex flex-col gap-4">
            <h2 id="booking-status" className="text-2xl font-bold text-ocean-900">
              {t("statusTitle")} <span className="text-sunset-700">{t(`status.${status}`)}</span>
            </h2>
            <ol className="grid gap-3 sm:grid-cols-3">
              {STEPS.map((step, index) => {
                const done = index < reached;
                const failed = stopped && index === 1;
                return (
                  <li
                    key={step}
                    aria-current={index === (stopped ? 1 : reached - 1) ? "step" : undefined}
                    className={cn(
                      "flex items-center gap-2 rounded-2xl border p-3 text-sm font-semibold",
                      failed ? "border-rose-200 bg-rose-50 text-rose-800" : done ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "text-muted-foreground",
                    )}
                  >
                    {failed ? (
                      <XIcon aria-hidden="true" className="size-4 shrink-0" />
                    ) : done ? (
                      <CheckIcon aria-hidden="true" className="size-4 shrink-0" />
                    ) : (
                      <CircleIcon aria-hidden="true" className="size-4 shrink-0" />
                    )}
                    {failed ? t(`stopped.${status}`) : t(`steps.${step}`)}
                  </li>
                );
              })}
            </ol>
            <p className="rounded-2xl bg-ocean-50 p-5 text-ocean-950">
              {status === "PENDING" && booking.expires_at
                ? t("statusText.PENDING", {
                    date: formatDate(booking.expires_at, lang, { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }),
                  })
                : t(`statusText.${status}`)}
            </p>
          </section>

          <section aria-labelledby="booking-items" className="flex flex-col gap-4 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="booking-items" className="text-2xl font-bold text-ocean-900">
              {t("itemsTitle")}
            </h2>
            {booking.items.length > 0 ? (
              <ul className="flex flex-col divide-y">
                {booking.items.map((item, index) => (
                  <li key={index} className="flex flex-col gap-2 py-4 first:pt-0 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex flex-col gap-1">
                      <span className="text-xs font-semibold uppercase tracking-wider text-sunset-700">{t(`kind.${item.kind}`)}</span>
                      <Link href={`${FICHE[item.kind]}/${item.target_slug}`} className="font-semibold text-ocean-950 hover:underline">
                        {item.label}
                      </Link>
                      <span className="flex items-center gap-2 text-sm text-ocean-950">
                        <CalendarDaysIcon aria-hidden="true" className="size-4 shrink-0 text-ocean-600" />
                        {item.kind === "activity"
                          ? day(item.start_date)
                          : t(`period.${item.kind}`, {
                              start: day(item.start_date),
                              // Fin exclue : le circuit se termine la veille.
                              end: day(item.kind === "tour_departure" ? addDays(item.end_date, -1) : item.end_date),
                            })}
                      </span>
                      {(item.quantity ?? 1) > 1 && <span className="text-sm text-muted-foreground">{t(`quantity.${item.kind}`, { count: item.quantity ?? 1 })}</span>}
                      {(item.pickup_location || item.dropoff_location) && (
                        <span className="text-sm text-muted-foreground">
                          {[item.pickup_location && t("pickup", { place: item.pickup_location }), item.dropoff_location && t("dropoff", { place: item.dropoff_location })]
                            .filter(Boolean)
                            .join(" · ")}
                        </span>
                      )}
                    </div>
                    <Price value={item.line_total} compact className="shrink-0 sm:items-end" />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-ocean-950">{t("fromQuote", { reference: booking.quote_reference ?? "" })}</p>
            )}
            <div className="flex items-center justify-between gap-4 border-t pt-4">
              <span className="font-semibold text-ocean-900">{t("total")}</span>
              <Price value={booking.total_amount} className="items-end" />
            </div>
            <p className="text-sm text-muted-foreground">{t("totalNote")}</p>
          </section>

          {booking.can_cancel && (
            <section aria-labelledby="booking-cancel" className="flex flex-col gap-3">
              <h2 id="booking-cancel" className="text-xl font-bold text-ocean-900">
                {t("cancelTitle")}
              </h2>
              <p className="text-ocean-950">{t("cancelText")}</p>
              <BookingCancel reference={booking.reference ?? reference} token={token} />
            </section>
          )}
        </div>

        <aside aria-labelledby="booking-summary" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-4 rounded-3xl border bg-card p-6">
            <h2 id="booking-summary" className="text-xl font-bold text-ocean-900">
              {t("summaryTitle")}
            </h2>
            <dl className="flex flex-col gap-3 text-sm">
              {[
                { label: t("reference"), value: booking.reference ?? reference },
                { label: t("sentOn"), value: formatDate(booking.created_at, lang, { day: "numeric", month: "long", year: "numeric" }) },
                { label: t("contact"), value: [booking.contact_name, booking.contact_email, booking.contact_phone].join("\n") },
                booking.quote_reference ? { label: t("quote"), value: booking.quote_reference } : null,
                booking.customer_comments ? { label: t("comments"), value: booking.customer_comments } : null,
              ]
                .filter((row) => row !== null)
                .map(({ label, value }) => (
                  <div key={label} className="flex flex-col gap-0.5">
                    <dt className="text-muted-foreground">{label}</dt>
                    <dd className="whitespace-pre-line break-words font-semibold text-ocean-950">{value}</dd>
                  </div>
                ))}
            </dl>
            <p className="border-t pt-4 text-sm text-ocean-950">
              {t("keepLink")}{" "}
              <Link href="/contact" className="font-semibold text-ocean-700 underline">
                {t("contactUs")}
              </Link>
            </p>
          </div>
        </aside>
      </Container>
    </>
  );
}
