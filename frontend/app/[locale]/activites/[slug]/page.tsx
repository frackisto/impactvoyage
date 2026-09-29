import { CheckCircle2Icon, ClockIcon, MapPinIcon, TagIcon, UsersIcon, XCircleIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { ActivityCard } from "@/components/activities/activity-card";
import { DateForm } from "@/components/activities/date-form";
import { Container } from "@/components/common/container";
import { ImmersiveHero } from "@/components/common/immersive-hero";
import { Section, SectionHeader } from "@/components/common/page-section";
import { Price } from "@/components/common/price";
import { SocialIcon } from "@/components/common/social-icons";
import { Gallery } from "@/components/media/gallery";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { countryFlag } from "@/lib/countries";
import { formatDate, formatHours, multiplyMoney } from "@/lib/format";
import { mediaSrc } from "@/lib/media";
import { pageHref } from "@/lib/pagination";
import { dateParam, intParam } from "@/lib/search-params";
import { absoluteUrl, pageMetadata, SITE_URL } from "@/lib/seo";
import { excerpt, paragraphs } from "@/lib/text";
import { cn } from "@/lib/utils";
import { activityAvailability, getActivity, relatedActivities } from "@/services/activities.service";
import { getSiteSettings, whatsappUrl } from "@/services/site.service";
import type { ActivityDetail } from "@/types";

type Props = PageProps<"/[locale]/activites/[slug]">;

function summary(activity: ActivityDetail) {
  return excerpt(activity.short_description || activity.description);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const activity = await getActivity(slug);
  if (!activity) notFound();
  return pageMetadata({
    locale,
    path: `/activites/${slug}`,
    title: activity.title,
    description: summary(activity),
    image: mediaSrc(activity.cover_image),
    imageAlt: activity.cover_alt || activity.title,
  });
}

export default async function ActivityPage({ params, searchParams }: Props) {
  const [{ locale, slug }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const activity = await getActivity(slug);
  if (!activity) notFound();

  const date = dateParam(query, "date");
  const participants = intParam(query, "participants", 1, 50) ?? 1;
  const [t, tNav, availability, related, settings] = await Promise.all([
    getTranslations("Activities"),
    getTranslations("Nav"),
    date ? activityAvailability(slug, date, participants) : Promise.resolve(null),
    relatedActivities(activity),
    getSiteSettings(),
  ]);

  const breadcrumbs = [{ label: t("title"), href: "/activites" }, { label: activity.title }];
  const price = activity.promo_price ?? activity.price;
  const total = price ? multiplyMoney(price, participants) : null;
  const whatsapp = whatsappUrl(settings.whatsapp);
  const dateQuery = { activity: activity.slug, date, participants: participants > 1 ? String(participants) : undefined };
  const requestHref = pageHref("/devis", dateQuery, 1);
  const bookHref = pageHref("/reservation", dateQuery, 1);
  const image = mediaSrc(activity.cover_image);
  const day = date ? formatDate(`${date}T00:00:00Z`, locale, { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }) : "";

  const facts = [
    { icon: ClockIcon, label: t("duration"), value: formatHours(activity.duration_hours, locale) },
    { icon: MapPinIcon, label: t("destination"), value: `${countryFlag(activity.destination.country_code)} ${activity.destination.name}` },
    activity.category ? { icon: TagIcon, label: t("categoryLabel"), value: activity.category.name } : null,
    {
      icon: UsersIcon,
      label: t("group"),
      value: activity.max_participants ? t("groupMax", { count: activity.max_participants }) : t("noLimit"),
    },
  ].filter((fact) => fact !== null);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "TouristTrip",
              name: activity.title,
              description: summary(activity),
              url: absoluteUrl(`/activites/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              touristType: activity.category?.name,
              offers: price ? { "@type": "Offer", price: price.amount, priceCurrency: price.currency } : undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/activites/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={activity.cover_image}
        imageAlt={activity.cover_alt || activity.title}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <MapPinIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {countryFlag(activity.destination.country_code)} {activity.destination.name}
            {activity.category ? ` · ${activity.category.name}` : ""}
          </>
        }
        title={activity.title}
        subtitle={activity.short_description}
      >
        <ul className="flex flex-wrap gap-2 text-sm font-semibold">
          <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
            <ClockIcon aria-hidden="true" className="size-4" /> {formatHours(activity.duration_hours, locale)}
          </li>
          {activity.max_participants ? (
            <li className="inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1 text-ocean-900">
              <UsersIcon aria-hidden="true" className="size-4" /> {t("groupMax", { count: activity.max_participants })}
            </li>
          ) : null}
        </ul>
      </ImmersiveHero>

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <div className="flex flex-col gap-12">
          <section aria-labelledby="activity-about" className="flex flex-col gap-5">
            <h2 id="activity-about" className="text-3xl font-bold text-ocean-900">
              {t("about")}
            </h2>
            {paragraphs(activity.description).map((p, i) => (
              <p key={i} className="text-lg leading-relaxed text-ocean-950/90">
                {p}
              </p>
            ))}
            <dl className="grid gap-4 rounded-2xl bg-ocean-50/70 p-5 sm:grid-cols-2">
              {facts.map(({ icon: Icon, label, value }) => (
                <div key={label} className="flex flex-col gap-0.5">
                  <dt className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Icon aria-hidden="true" className="size-5 shrink-0 text-ocean-600" />
                    {label}
                  </dt>
                  <dd className="ps-7 font-semibold text-ocean-950">{value}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section id="disponibilites" aria-labelledby="activity-availability" className="flex scroll-mt-24 flex-col gap-5">
            <h2 id="activity-availability" className="text-3xl font-bold text-ocean-900">
              {t("availabilityTitle")}
            </h2>
            <DateForm
              pathname={`/activites/${slug}`}
              date={date}
              participants={participants}
              maxParticipants={activity.max_participants}
            />
            {date &&
              (availability ? (
                <div
                  role="status"
                  className={cn(
                    "flex flex-col gap-3 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between",
                    availability.available ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50",
                  )}
                >
                  <div className="flex flex-col gap-1">
                    <p
                      className={cn(
                        "inline-flex items-center gap-2 font-semibold",
                        availability.available ? "text-emerald-800" : "text-rose-800",
                      )}
                    >
                      {availability.available ? (
                        <CheckCircle2Icon aria-hidden="true" className="size-5 shrink-0" />
                      ) : (
                        <XCircleIcon aria-hidden="true" className="size-5 shrink-0" />
                      )}
                      {availability.places_left === null
                        ? t("availableNoLimit", { day })
                        : availability.available
                          ? t("availablePlaces", { day, count: availability.places_left })
                          : availability.places_left === 0
                            ? t("full", { day })
                            : t("notEnough", { day, count: availability.places_left })}
                    </p>
                    {availability.available && total && (
                      <p className="text-sm text-emerald-900">
                        {t("total", { count: participants })} <Price value={total} compact className="inline-flex" />
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
              ) : (
                <p role="status" className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-800">
                  {t("availabilityError")}
                </p>
              ))}
          </section>
        </div>

        <aside aria-labelledby="activity-booking" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="activity-booking" className="text-xl font-bold text-ocean-900">
              {t("bookTitle")}
            </h2>
            {activity.promo_price ? (
              <div className="flex flex-col">
                <Price value={activity.price} strikethrough />
                <Price value={activity.promo_price} unit="person" />
              </div>
            ) : (
              <Price value={activity.price} unit="person" />
            )}
            <div className="flex flex-col gap-2">
              <a href="#disponibilites" className={cn(buttonVariants({ variant: "cta", size: "lg" }), "w-full")}>
                {t("chooseDate")}
              </a>
              <Link href={requestHref} className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}>
                {t("request")}
              </Link>
              {whatsapp && (
                <a
                  href={`${whatsapp}?text=${encodeURIComponent(t("whatsappMessage", { title: activity.title }))}`}
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
        </aside>
      </Container>

      {activity.images.length > 0 && (
        <Section tone="tint" aria-labelledby="activity-gallery">
          <SectionHeader id="activity-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle")} />
          <Gallery
            title={activity.title}
            photos={activity.images.map((img) => ({ id: img.id, image: img.image, alt: img.alt_text || activity.title }))}
          />
        </Section>
      )}

      {related.length > 0 && (
        <Section aria-labelledby="activity-related">
          <SectionHeader
            id="activity-related"
            eyebrow={t("relatedEyebrow")}
            title={t("relatedTitle")}
            href="/activites"
            linkLabel={t("allActivities")}
          />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <ActivityCard activity={other} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
