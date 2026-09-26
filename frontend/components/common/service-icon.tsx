import {
  BookOpenIcon,
  CarIcon,
  CompassIcon,
  HotelIcon,
  HouseIcon,
  MapIcon,
  PartyPopperIcon,
  PlaneIcon,
  RefreshCcwIcon,
  ShieldCheckIcon,
  SparklesIcon,
  StampIcon,
  type LucideIcon,
} from "lucide-react";

/** Icônes des services (champ « icône » du service dans l'admin, nom Lucide). */
const ICONS: Record<string, LucideIcon> = {
  "book-open": BookOpenIcon,
  car: CarIcon,
  compass: CompassIcon,
  hotel: HotelIcon,
  house: HouseIcon,
  map: MapIcon,
  "party-popper": PartyPopperIcon,
  plane: PlaneIcon,
  "refresh-ccw": RefreshCcwIcon,
  "shield-check": ShieldCheckIcon,
  sparkles: SparklesIcon,
  stamp: StampIcon,
};

export function ServiceIcon({ name, className }: { name: string | undefined; className?: string }) {
  const Icon = (name && ICONS[name]) || CompassIcon;
  return <Icon aria-hidden="true" className={className} />;
}
