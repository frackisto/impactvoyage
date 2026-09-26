import { CogIcon, FuelIcon, SnowflakeIcon, UsersIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { Price } from "@/components/common/price";
import { pageHref } from "@/lib/pagination";
import type { VehicleList } from "@/types";

/** Nom affiché d'un véhicule (« Suzuki Vitara »). */
export const vehicleName = (vehicle: Pick<VehicleList, "brand" | "model">) => `${vehicle.brand} ${vehicle.model}`;

/**
 * Carte d'un véhicule : catégorie, places, boîte, carburant, climatisation et
 * prix par jour. `period` (dates) est transmise à la fiche pour la disponibilité.
 */
export function VehicleCard({ vehicle, period = {}, priority }: {
  vehicle: VehicleList;
  period?: Record<string, string | undefined>;
  priority?: boolean;
}) {
  const t = useTranslations("Vehicles");
  const name = vehicleName(vehicle);
  return (
    <ContentCard
      href={pageHref(`/vehicules/${vehicle.slug}`, period, 1)}
      title={name}
      eyebrow={t("categoryYear", { category: t(`category.${vehicle.category}`), year: vehicle.year })}
      image={vehicle.cover_image}
      imageAlt={vehicle.cover_alt || name}
      priority={priority}
      meta={
        <>
          <span className="inline-flex items-center gap-1">
            <UsersIcon aria-hidden="true" className="size-4" /> {t("seats", { count: vehicle.seats })}
          </span>
          <span className="inline-flex items-center gap-1">
            <CogIcon aria-hidden="true" className="size-4" /> {t(`transmission.${vehicle.transmission}`)}
          </span>
          <span className="inline-flex items-center gap-1">
            <FuelIcon aria-hidden="true" className="size-4" /> {t(`fuel.${vehicle.fuel}`)}
          </span>
          {vehicle.air_conditioning && (
            <span className="inline-flex items-center gap-1">
              <SnowflakeIcon aria-hidden="true" className="size-4" /> {t("airConditioning")}
            </span>
          )}
        </>
      }
      footer={<Price value={vehicle.price_per_day} from unit="day" />}
    />
  );
}
