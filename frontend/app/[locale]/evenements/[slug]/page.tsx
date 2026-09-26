import { CalendarDaysIcon, ExternalLinkIcon, MapPinIcon, PlayCircleIcon, TagIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { ImmersiveHero } from "@/components/common/immersive-hero";
import { Section, SectionHeader } from "@/components/common/page-section";
import { EventCard, eventDates } from "@/components/events/event-card";
import { Gallery } from "@/components/media/gallery";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { mediaSrc } from "@/lib/media";
import { absoluteUrl, alternates, SITE_URL } from "@/lib/seo";
import { excerpt, paragraphs } from "@/lib/text";
import { getEvent, relatedEvents } from "@/services/events.service";
import { getSiteSettings } from "@/services/site.service";
import type { EventDetail } from "@/types";

type Props = PageProps<"/[locale]/evenements/[slug]">;

function summary(event: EventDetail) {
  return excerpt(event.short_description || event.description);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const event = await getEvent(slug);
  if (!event) notFound();
  const image = mediaSrc(event.cover_image);
  return {
    title: event.title,
    description: summary(event),
    alternates: alternates(`/evenements/${slug}`, locale),
    openGraph: {
      type: "article",
      title: event.title,
      description: summary(event),
      url: absoluteUrl(`/evenements/${slug}`, locale),
      images: image ? [{ url: image, alt: event.cover_alt || event.title }] : undefined,
    },
  };
}

export default async function EventPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const event = await getEvent(slug);
  if (!event) notFound();

  const [t, tNav, lang, related, settings] = await Promise.all([
    getTranslations("Events"),
    getTranslations("Nav"),
    getLocale(),
    relatedEvents(event),
    getSiteSettings(),
  ]);

  const breadcrumbs = [{ label: t("title"), href: "/evenements" }, { label: event.title }];
  const photos = event.media.filter((m) => m.type === "PHOTO" && m.image);
  const videos = event.media.filter((m) => m.type === "VIDEO" && m.video_url);
  const image = mediaSrc(event.cover_image);

  const facts = [
    { icon: CalendarDaysIcon, label: t("dates"), value: eventDates(event, lang) },
    { icon: MapPinIcon, label: t("location"), value: event.location },
    { icon: TagIcon, label: t("categoryLabel"), value: t(`category.${event.category}`) },
    event.participants_count ? { icon: UsersIcon, label: t("participantsLabel"), value: t("participants", { count: event.participants_count }) } : null,
  ].filter((fact) => fact !== null);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Event",
              name: event.title,
              description: summary(event),
              url: absoluteUrl(`/evenements/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              startDate: event.date,
              endDate: event.end_date ?? event.date,
              eventStatus: "https://schema.org/EventScheduled",
              eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
              location: { "@type": "Place", name: event.location, address: event.location },
              organizer: settings.agency_name ? { "@type": "TravelAgency", name: settings.agency_name, url: SITE_URL } : undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/evenements/${slug}`, locale),
          ],
        }}
      />

      <ImmersiveHero
        image={event.cover_image}
        imageAlt={event.cover_alt || event.title}
        breadcrumbs={breadcrumbs}
        badge={
          <>
            <CalendarDaysIcon aria-hidden="true" className="size-4 text-sunset-300" />
            {t(`category.${event.category}`)} · {eventDates(event, lang)}
          </>
        }
        title={event.title}
        subtitle={event.short_description}
      />

      <Container className="grid gap-10 py-12 sm:py-16 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-14">
        <section aria-labelledby="event-about" className="flex flex-col gap-5">
          <h2 id="event-about" className="text-3xl font-bold text-ocean-900">
            {t("about")}
          </h2>
          {paragraphs(event.description).map((p, i) => (
            <p key={i} className="text-lg leading-relaxed text-ocean-950/90">
              {p}
            </p>
          ))}
          {event.partners.length > 0 && (
            <div className="flex flex-col gap-3">
              <h3 className="text-xl font-bold text-ocean-900">{t("partners")}</h3>
              <ul className="flex flex-wrap gap-2">
                {event.partners.map((partner) => (
                  <li key={partner.name}>
                    {partner.url ? (
                      <a
                        href={partner.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium text-ocean-900 hover:bg-ocean-50"
                      >
                        {partner.name} <ExternalLinkIcon aria-hidden="true" className="size-3.5" />
                      </a>
                    ) : (
                      <span className="inline-flex rounded-full border px-3 py-1.5 text-sm font-medium text-ocean-900">{partner.name}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <aside aria-labelledby="event-facts" className="lg:sticky lg:top-24 lg:self-start">
          <div className="flex flex-col gap-5 rounded-3xl border bg-card p-6 shadow-lg shadow-ocean-900/5">
            <h2 id="event-facts" className="text-xl font-bold text-ocean-900">
              {t("factsTitle")}
            </h2>
            <dl className="flex flex-col gap-3">
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
            {event.destination && (
              <Link href={`/destinations/${event.destination.slug}`} className={buttonVariants({ variant: "outline" })}>
                {t("seeDestination", { name: event.destination.name })}
              </Link>
            )}
          </div>
        </aside>
      </Container>

      {photos.length > 0 && (
        <Section tone="tint" aria-labelledby="event-gallery">
          <SectionHeader id="event-gallery" eyebrow={t("galleryEyebrow")} title={t("galleryTitle")} />
          <Gallery title={event.title} photos={photos.map((m) => ({ id: m.id, image: m.image, alt: m.alt_text || event.title }))} />
        </Section>
      )}

      {videos.length > 0 && (
        <Section aria-labelledby="event-videos">
          <SectionHeader id="event-videos" eyebrow={t("galleryEyebrow")} title={t("videosTitle")} />
          {/* Lien vers la plateforme vidéo (YouTube, Vimeo) plutôt qu'un lecteur intégré. */}
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {videos.map((video, index) => (
              <li key={video.id}>
                <a
                  href={video.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-2xl border bg-card p-5 font-semibold text-ocean-900 hover:border-ocean-300 hover:shadow-md"
                >
                  <PlayCircleIcon aria-hidden="true" className="size-8 shrink-0 text-sunset-600" />
                  {video.alt_text || t("video", { number: index + 1 })}
                  <span className="sr-only">{t("newTab")}</span>
                </a>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <section aria-labelledby="event-organize" className="bg-gradient-to-r from-ocean-700 to-ocean-900 py-14 text-white">
        <Container className="flex flex-col items-center justify-between gap-6 text-center lg:flex-row lg:text-start">
          <div className="flex max-w-2xl flex-col gap-2">
            <h2 id="event-organize" className="text-3xl font-bold">
              {t("organizeTitle")}
            </h2>
            <p className="text-lg text-ocean-100">{t("organizeText")}</p>
          </div>
          <Link href="/devis?service=EVENEMENT" className={buttonVariants({ variant: "cta", size: "lg" })}>
            {t("organizeCta")}
          </Link>
        </Container>
      </section>

      {related.length > 0 && (
        <Section tone="tint" aria-labelledby="event-related">
          <SectionHeader id="event-related" eyebrow={t("relatedEyebrow")} title={t("relatedTitle")} href="/evenements" linkLabel={t("allEvents")} />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <EventCard event={other} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
