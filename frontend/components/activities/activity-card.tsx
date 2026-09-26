import { ClockIcon, TicketIcon, UsersIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { Price } from "@/components/common/price";
import { formatHours } from "@/lib/format";
import { pageHref } from "@/lib/pagination";
import type { ActivityList, Schemas } from "@/types";

/** Carte complète (liste) ou réduite (activités d'une destination ou d'un circuit). */
export type ActivityCardData = Schemas["ActivityCard"] &
  Partial<Pick<ActivityList, "destination" | "category" | "max_participants" | "places_left">>;

/**
 * Carte d'une activité : catégorie, destination, durée, taille du groupe, prix
 * par personne ; avec une date choisie, les places restantes ce jour-là.
 */
export function ActivityCard({ activity, query = {}, priority, showDestination = true }: {
  activity: ActivityCardData;
  /** Date et participants transmis à la fiche. */
  query?: Record<string, string | undefined>;
  priority?: boolean;
  showDestination?: boolean;
}) {
  const t = useTranslations("Activities");
  const locale = useLocale();
  const placesLeft = activity.places_left;

  return (
    <ContentCard
      href={pageHref(`/activites/${activity.slug}`, query, 1)}
      title={activity.title}
      eyebrow={showDestination ? activity.destination?.name : undefined}
      description={activity.short_description}
      image={activity.cover_image}
      imageAlt={activity.cover_alt || activity.title}
      priority={priority}
      badges={
        activity.category ? (
          <span className="rounded-4xl bg-white/95 px-2.5 py-0.5 text-xs font-semibold text-ocean-900">{activity.category.name}</span>
        ) : undefined
      }
      meta={
        <>
          <span className="inline-flex items-center gap-1">
            <ClockIcon aria-hidden="true" className="size-4" /> {formatHours(activity.duration_hours, locale)}
          </span>
          {activity.max_participants ? (
            <span className="inline-flex items-center gap-1">
              <UsersIcon aria-hidden="true" className="size-4" /> {t("groupMax", { count: activity.max_participants })}
            </span>
          ) : null}
          {placesLeft !== undefined && placesLeft !== null && (
            <span className="inline-flex items-center gap-1 font-medium text-emerald-800">
              <TicketIcon aria-hidden="true" className="size-4" /> {t("placesLeft", { count: placesLeft })}
            </span>
          )}
        </>
      }
      footer={<Price value={activity.price} from unit="person" />}
    />
  );
}
