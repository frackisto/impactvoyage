import { CalendarDaysIcon, CalendarSearchIcon, ClipboardCheckIcon, HeadsetIcon, MailCheckIcon, SearchXIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { BookingForm } from "@/components/booking/booking-form";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { SocialIcon } from "@/components/common/social-icons";
import { EmptyState } from "@/components/common/states";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { mediaSrc } from "@/lib/media";
import { pageHref } from "@/lib/pagination";
import { param, type SearchParams } from "@/lib/search-params";
import { cn } from "@/lib/utils";
import { bookingDraft, type BookingDraft } from "@/services/bookings.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";

type Props = PageProps<"/[locale]/reservation">;

/** Paramètres communs aux liens de réservation et de devis (même préremplissage). */
const LINK_KEYS = ["tour", "departure", "hotel", "room", "residence", "vehicle", "activity", "start", "end", "date", "travelers", "rooms", "participants"];

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Booking" });
  // Page de formulaire préremplie, sans contenu propre : jamais indexée.
  return { title: t("title"), description: t("intro"), robots: { index: false, follow: true } };
}

/**
 * Demande de réservation en ligne (CdC § 12, § 13), ouverte depuis une fiche :
 * départ de circuit, chambre, résidence, véhicule ou activité, avec les dates
 * choisies. L'agence confirme ; le client suit sa demande par le lien reçu.
 */
export default async function BookingPage({ params, searchParams }: Props) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const [t, draft, settings] = await Promise.all([getTranslations("Booking"), bookingDraft(query), getSiteSettings()]);
  const whatsapp = whatsappUrl(settings.whatsapp);
  const quoteHref = pageHref("/devis", linkQuery(query), 1);

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-8">
          {!draft ? (
            <EmptyState
              icon={SearchXIcon}
              title={t("noOfferTitle")}
              description={t("noOfferText")}
              action={
                <div className="flex flex-wrap justify-center gap-3">
                  {(["/circuits/nationaux", "/hotels", "/vehicules", "/activites"] as const).map((href) => (
                    <Link key={href} href={href} className={buttonVariants({ variant: "outline" })}>
                      {t(`browse.${href.split("/")[1]}`)}
                    </Link>
                  ))}
                </div>
              }
            />
          ) : (
            <>
              <DraftCard draft={draft} />
              {draft.needsDates ? (
                <Notice
                  icon={CalendarSearchIcon}
                  text={t(draft.kind === "tour_departure" ? "needsDeparture" : "needsDates")}
                  href={`${draft.href}#${draft.kind === "tour_departure" ? "reserver" : "disponibilites"}`}
                  action={t(draft.kind === "tour_departure" ? "chooseDeparture" : "chooseDates")}
                />
              ) : !draft.available ? (
                <Notice icon={SearchXIcon} tone="warning" text={t("unavailable")} href={`${draft.href}#disponibilites`} action={t("otherDates")}>
                  <Link href={quoteHref} className={buttonVariants({ variant: "outline" })}>
                    {t("askQuote")}
                  </Link>
                </Notice>
              ) : (
                <BookingForm
                  item={{
                    kind: draft.kind,
                    objectId: draft.objectId,
                    start: draft.start,
                    end: draft.end,
                    quantityKind: draft.quantityKind,
                    quantity: draft.quantity,
                    maxQuantity: draft.maxQuantity,
                    unitPrice: draft.unitPrice,
                    periods: Math.max(draft.periods, 1),
                    withLocations: draft.withLocations,
                    href: draft.href,
                  }}
                />
              )}
            </>
          )}
        </div>

        <aside aria-labelledby="booking-how" className="flex flex-col gap-6 lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-4 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="booking-how" className="text-xl font-bold text-ocean-900">
              {t("howTitle")}
            </h2>
            <ol className="flex flex-col gap-3 text-sm text-ocean-950">
              {[
                { icon: MailCheckIcon, text: t("how1") },
                { icon: ClipboardCheckIcon, text: t("how2") },
                { icon: HeadsetIcon, text: t("how3") },
              ].map(({ icon: Icon, text }) => (
                <li key={text} className="flex gap-3">
                  <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sunset-600" />
                  {text}
                </li>
              ))}
            </ol>
            {draft && (
              <p className="border-t pt-4 text-sm text-ocean-950">
                {t("preferQuote")}{" "}
                <Link href={quoteHref} className="font-semibold text-ocean-700 underline">
                  {t("askQuote")}
                </Link>
              </p>
            )}
          </div>
          {(settings.phone || whatsapp) && (
            <div className="flex flex-col gap-3 rounded-3xl bg-ocean-900 p-6 text-white">
              <p className="font-heading text-lg font-bold">{t("questions")}</p>
              {settings.phone && (
                <a href={`tel:${settings.phone.replace(/\s/g, "")}`} className={cn(buttonVariants({ variant: "inverse" }), "w-full")}>
                  {settings.phone}
                </a>
              )}
              {whatsapp && (
                <a
                  href={whatsapp}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(buttonVariants({ variant: "outline" }), "w-full border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white")}
                >
                  <SocialIcon network="whatsapp" className="size-5" />
                  WhatsApp
                </a>
              )}
            </div>
          )}
        </aside>
      </Container>
    </>
  );
}

function linkQuery(query: SearchParams) {
  return Object.fromEntries(LINK_KEYS.map((key) => [key, param(query, key)]));
}

/** Rappel de la prestation choisie : photo, dates, voyageurs et tarif unitaire. */
async function DraftCard({ draft }: { draft: BookingDraft }) {
  const [t, locale] = await Promise.all([getTranslations("Booking"), getLocale()]);
  const date = (value: string) =>
    formatDate(`${value}T00:00:00Z`, locale, { weekday: "short", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const image = mediaSrc(draft.image);
  const dates =
    draft.displayStart && draft.displayEnd && draft.displayEnd !== draft.displayStart
      ? t(`period.${draft.kind}`, { start: date(draft.displayStart), end: date(draft.displayEnd) })
      : draft.displayStart
        ? date(draft.displayStart)
        : null;
  const unit = draft.periodUnit ?? (draft.kind === "room" ? "night" : "person");

  return (
    <section aria-labelledby="booking-offer" className="flex flex-col gap-4 rounded-3xl border bg-ocean-50/70 p-4 sm:flex-row sm:items-center">
      {image && (
        <span className="relative h-40 w-full shrink-0 overflow-hidden rounded-2xl sm:h-24 sm:w-32">
          <Image src={image} alt="" fill sizes="(min-width: 640px) 128px, 100vw" className="object-cover" />
        </span>
      )}
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-sunset-700">{t(`kind.${draft.kind}`)}</p>
        <h2 id="booking-offer" className="text-lg font-bold text-ocean-900">
          <Link href={draft.href} className="hover:underline">
            {draft.title}
          </Link>
        </h2>
        {draft.detail && <p className="font-semibold text-ocean-950">{draft.detail}</p>}
        {dates && (
          <p className="flex items-center gap-2 text-sm text-ocean-950">
            <CalendarDaysIcon aria-hidden="true" className="size-4 shrink-0 text-ocean-600" />
            {dates}
            {draft.periods > 0 && draft.periodUnit && <span className="text-muted-foreground">· {t(`periods.${draft.periodUnit}`, { count: draft.periods })}</span>}
          </p>
        )}
        {draft.kind === "tour_departure" && draft.available && (
          <p className="flex items-center gap-2 text-sm text-ocean-950">
            <UsersIcon aria-hidden="true" className="size-4 shrink-0 text-ocean-600" />
            {t("seatsLeft", { count: draft.maxQuantity })}
          </p>
        )}
      </div>
      {draft.unitPrice && <Price value={draft.unitPrice} unit={unit} compact className="shrink-0" />}
    </section>
  );
}

function Notice({ icon: Icon, text, href, action, tone = "info", children }: {
  icon: typeof CalendarSearchIcon;
  text: string;
  href: string;
  action: string;
  tone?: "info" | "warning";
  children?: React.ReactNode;
}) {
  return (
    <div
      role="status"
      className={cn(
        "flex flex-col items-start gap-4 rounded-3xl border p-6",
        tone === "warning" ? "border-rose-200 bg-rose-50" : "border-ocean-200 bg-ocean-50",
      )}
    >
      <p className={cn("flex gap-3 text-lg", tone === "warning" ? "text-rose-900" : "text-ocean-950")}>
        <Icon aria-hidden="true" className="mt-1 size-5 shrink-0" />
        {text}
      </p>
      <div className="flex flex-wrap gap-3">
        <Link href={href} className={buttonVariants({ variant: "cta" })}>
          {action}
        </Link>
        {children}
      </div>
    </div>
  );
}
