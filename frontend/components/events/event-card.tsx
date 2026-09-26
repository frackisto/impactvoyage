import { CalendarDaysIcon, MapPinIcon, UsersIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { formatDate, intlLocale } from "@/lib/format";
import type { EventList } from "@/types";

/** Période d'un événement : « 16 février 2025 » ou « 14 – 20 mars 2026 ». */
export function eventDates(event: Pick<EventList, "date" | "end_date">, locale: string) {
  const start = new Date(`${event.date}T00:00:00Z`);
  const long = { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" } as const;
  if (!event.end_date || event.end_date === event.date) return formatDate(start, locale, long);
  return new Intl.DateTimeFormat(intlLocale(locale), long).formatRange(start, new Date(`${event.end_date}T00:00:00Z`));
}

/** Carte d'un événement réalisé par l'agence (CdC § 15). */
export function EventCard({ event, priority, participants }: { event: EventList; priority?: boolean; participants?: number | null }) {
  const t = useTranslations("Events");
  const locale = useLocale();
  return (
    <ContentCard
      href={`/evenements/${event.slug}`}
      title={event.title}
      description={event.short_description}
      image={event.cover_image}
      imageAlt={event.cover_alt || event.title}
      priority={priority}
      badges={
        <span className="rounded-4xl bg-white/95 px-2.5 py-0.5 text-xs font-semibold text-ocean-900">
          {t(`category.${event.category}`)}
        </span>
      }
      meta={
        <>
          <span className="inline-flex items-center gap-1">
            <CalendarDaysIcon aria-hidden="true" className="size-4" /> {eventDates(event, locale)}
          </span>
          <span className="inline-flex items-center gap-1">
            <MapPinIcon aria-hidden="true" className="size-4" /> {event.location}
          </span>
          {participants ? (
            <span className="inline-flex items-center gap-1">
              <UsersIcon aria-hidden="true" className="size-4" /> {t("participants", { count: participants })}
            </span>
          ) : null}
        </>
      }
    />
  );
}
