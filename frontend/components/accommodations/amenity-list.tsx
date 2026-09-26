import {
  AirVentIcon,
  BedDoubleIcon,
  BusIcon,
  CheckIcon,
  CoffeeIcon,
  CookingPotIcon,
  SquareParkingIcon,
  SunsetIcon,
  TvIcon,
  UtensilsIcon,
  WavesIcon,
  WifiIcon,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { Amenity } from "@/types";

/** Icônes des équipements (champ « icône » de l'admin, nom Lucide) ; coche par défaut. */
const ICONS: Record<string, LucideIcon> = {
  "air-vent": AirVentIcon,
  "bed-double": BedDoubleIcon,
  bus: BusIcon,
  coffee: CoffeeIcon,
  "cooking-pot": CookingPotIcon,
  "square-parking": SquareParkingIcon,
  sunset: SunsetIcon,
  tv: TvIcon,
  utensils: UtensilsIcon,
  waves: WavesIcon,
  wifi: WifiIcon,
};

export function AmenityIcon({ name, className }: { name?: string; className?: string }) {
  const Icon = (name && ICONS[name]) || CheckIcon;
  return <Icon aria-hidden="true" className={className} />;
}

/** Équipements d'un hébergement (CdC § 13, § 14). */
export function AmenityList({ amenities, className }: { amenities: Amenity[]; className?: string }) {
  return (
    <ul className={cn("grid gap-3 sm:grid-cols-2 lg:grid-cols-3", className)}>
      {amenities.map((amenity) => (
        <li key={amenity.id} className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3 text-ocean-950">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-ocean-50 text-ocean-700">
            <AmenityIcon name={amenity.icon} className="size-5" />
          </span>
          {amenity.name}
        </li>
      ))}
    </ul>
  );
}
