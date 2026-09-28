import { CheckIcon, CircleIcon, LinkIcon, XIcon } from "lucide-react";
import type { Metadata } from "next";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { EmptyState } from "@/components/common/states";
import { QuoteAnswer } from "@/components/quotes/quote-answer";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { param } from "@/lib/search-params";
import { paragraphs } from "@/lib/text";
import { cn } from "@/lib/utils";
import { getClientQuote } from "@/services/quotes.service";
import type { QuoteClient } from "@/types";

type Props = PageProps<"/[locale]/devis/[reference]">;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, reference } = await params;
  const t = await getTranslations({ locale, namespace: "QuoteTracking" });
  // Page personnelle (lien secret) : jamais indexée.
  return { title: t("metaTitle", { reference }), robots: { index: false, follow: false } };
}

const STEPS = ["NOUVELLE", "EN_COURS", "DEVIS_ENVOYE", "ACCEPTEE"] as const;

/** Étapes franchies : la demande avance de la réception à l'acceptation (ou au refus). */
function progress(status: QuoteClient["status"]) {
  if (status === "REFUSEE") return { reached: 3, declined: true };
  if (status === "TERMINEE") return { reached: 4, declined: false };
  return { reached: STEPS.indexOf(status as (typeof STEPS)[number]) + 1, declined: false };
}

/**
 * Suivi d'une demande de devis par le client (CdC § 18, § 38), sans compte :
 * lien reçu par email /devis/{reference}?token=…
 */
export default async function QuoteTrackingPage({ params, searchParams }: Props) {
  const [{ locale, reference }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("QuoteTracking");
  const lang = await getLocale();
  const token = param(query, "token") ?? "";
  const quote = token ? await getClientQuote(reference, token).catch(() => null) : null;

  if (!quote) {
    return (
      <>
        <PageHeader title={t("invalidTitle")} breadcrumbs={[{ label: t("breadcrumb") }]} />
        <Container className="py-12">
          <EmptyState
            icon={LinkIcon}
            title={t("invalidTitle")}
            description={t("invalidText")}
            action={
              <div className="flex flex-wrap justify-center gap-3">
                <Link href="/devis" className={buttonVariants({ variant: "cta" })}>
                  {t("newQuote")}
                </Link>
              </div>
            }
          />
        </Container>
      </>
    );
  }

  const date = (value: string) => formatDate(`${value}T00:00:00Z`, lang, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const { reached, declined } = progress(quote.status);
  const travelers = [
    t("adults", { count: quote.adults ?? 1 }),
    quote.children ? t("children", { count: quote.children }) : null,
  ].filter(Boolean);

  return (
    <>
      <PageHeader
        title={t("title", { reference: quote.reference ?? reference })}
        description={t("hello", { name: quote.first_name })}
        breadcrumbs={[{ label: t("breadcrumb") }]}
      />
      <Container className="grid gap-10 py-10 sm:py-14 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-8">
          <section aria-labelledby="quote-status" className="flex flex-col gap-4">
            <h2 id="quote-status" className="text-2xl font-bold text-ocean-900">
              {t("statusTitle")} <span className="text-sunset-700">{t(`status.${quote.status}`)}</span>
            </h2>
            <ol className="grid gap-3 sm:grid-cols-4">
              {STEPS.map((step, index) => {
                const done = index < reached;
                const refused = declined && step === "ACCEPTEE";
                return (
                  <li
                    key={step}
                    aria-current={index === reached - 1 ? "step" : undefined}
                    className={cn(
                      "flex items-center gap-2 rounded-2xl border p-3 text-sm font-semibold",
                      refused ? "border-rose-200 bg-rose-50 text-rose-800" : done ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "text-muted-foreground",
                    )}
                  >
                    {refused ? (
                      <XIcon aria-hidden="true" className="size-4 shrink-0" />
                    ) : done ? (
                      <CheckIcon aria-hidden="true" className="size-4 shrink-0" />
                    ) : (
                      <CircleIcon aria-hidden="true" className="size-4 shrink-0" />
                    )}
                    {refused ? t("steps.REFUSEE") : t(`steps.${step}`)}
                  </li>
                );
              })}
            </ol>
          </section>

          {quote.proposal_amount || quote.proposal_message ? (
            <section aria-labelledby="quote-proposal" className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
              <h2 id="quote-proposal" className="text-2xl font-bold text-ocean-900">
                {t("proposalTitle")}
              </h2>
              {quote.proposal_amount && (
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted-foreground">{t("amount")}</span>
                  <Price value={quote.proposal_amount} />
                </div>
              )}
              <div className="flex flex-col gap-3 text-ocean-950">
                {paragraphs(quote.proposal_message).map((p, i) => (
                  <p key={i} className="whitespace-pre-line">
                    {p}
                  </p>
                ))}
              </div>
              {quote.proposal_valid_until && (
                <p className="text-sm text-muted-foreground">{t("validUntil", { date: date(quote.proposal_valid_until) })}</p>
              )}
              {quote.can_answer ? (
                <QuoteAnswer reference={quote.reference ?? reference} token={token} />
              ) : quote.status === "DEVIS_ENVOYE" ? (
                <p className="rounded-2xl bg-sunset-50 p-4 text-ocean-950">{t("expired")}</p>
              ) : null}
              {quote.booking_reference && (
                <p role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
                  {t("acceptedText", { reference: quote.booking_reference })}
                </p>
              )}
            </section>
          ) : (
            <p className="rounded-3xl bg-ocean-50 p-6 text-lg text-ocean-950">{t("pending")}</p>
          )}
        </div>

        <aside aria-labelledby="quote-summary" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-4 rounded-3xl border bg-card p-6">
            <h2 id="quote-summary" className="text-xl font-bold text-ocean-900">
              {t("summaryTitle")}
            </h2>
            <dl className="flex flex-col gap-3 text-sm">
              {[
                { label: t("destination"), value: quote.destination_label || "—" },
                {
                  label: t("dates"),
                  value:
                    quote.date_departure && quote.date_return
                      ? t("period", { start: date(quote.date_departure), end: date(quote.date_return) })
                      : quote.date_departure
                        ? date(quote.date_departure)
                        : t("flexible"),
                },
                { label: t("travelers"), value: travelers.join(", ") },
                { label: t("sentOn"), value: formatDate(quote.created_at, lang, { day: "numeric", month: "long", year: "numeric" }) },
              ].map(({ label, value }) => (
                <div key={label} className="flex flex-col gap-0.5">
                  <dt className="text-muted-foreground">{label}</dt>
                  <dd className="font-semibold text-ocean-950">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </aside>
      </Container>
    </>
  );
}
