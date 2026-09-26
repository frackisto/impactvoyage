import { CheckCircle2Icon, UsersIcon, XCircleIcon } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Price } from "@/components/common/price";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { multiplyMoney } from "@/lib/format";
import { pageHref } from "@/lib/pagination";
import { nights, stayQuery, type Stay } from "@/lib/stay";
import { cn } from "@/lib/utils";
import type { HotelDetail, RoomAvailability } from "@/types";

/**
 * Types de chambres d'un hôtel avec leur prix par nuit. Avec des dates : chambres
 * libres, total indicatif du séjour et demande de devis préremplie.
 */
export async function RoomList({ hotel, stay, availability }: {
  hotel: HotelDetail;
  stay: Stay;
  availability: RoomAvailability[] | null;
}) {
  const t = await getTranslations("Stays");
  const count = nights(stay.start, stay.end);
  const rooms = stay.rooms ?? 1;
  const byRoom = new Map((availability ?? []).map((row) => [row.room, row]));

  return (
    <ul className="flex flex-col gap-4">
      {hotel.rooms.map((room) => {
        const status = availability ? byRoom.get(room.id) : undefined;
        const total = count && room.price_per_night ? multiplyMoney(room.price_per_night, count * rooms) : null;
        const href = pageHref("/devis", { hotel: hotel.slug, room: String(room.id), ...stayQuery(stay) }, 1);
        return (
          <li key={room.id} className="flex flex-col gap-4 rounded-2xl border bg-card p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-1.5">
              <h3 className="text-lg font-semibold text-ocean-950">{room.name}</h3>
              {room.description && <p className="text-sm text-muted-foreground">{room.description}</p>}
              <span className="inline-flex items-center gap-1.5 text-sm text-ocean-800">
                <UsersIcon aria-hidden="true" className="size-4" /> {t("guests", { count: room.capacity })}
              </span>
              {status && (
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 text-sm font-semibold",
                    status.available ? "text-emerald-700" : "text-rose-700",
                  )}
                >
                  {status.available ? (
                    <CheckCircle2Icon aria-hidden="true" className="size-4" />
                  ) : (
                    <XCircleIcon aria-hidden="true" className="size-4" />
                  )}
                  {status.available
                    ? t("roomsLeft", { count: status.units_left })
                    : status.fits
                      ? t("fullOnDates")
                      : t("tooSmall")}
                </span>
              )}
            </div>
            <div className="flex shrink-0 flex-col gap-2 sm:items-end">
              <Price value={room.price_per_night} unit="night" />
              {total && (
                <span className="text-sm text-muted-foreground">
                  {t("totalFor", { nights: count, rooms })} <Price value={total} compact className="inline-flex" />
                </span>
              )}
              <Link
                href={href}
                aria-label={t("requestRoom", { room: room.name })}
                className={cn(buttonVariants({ variant: status && !status.available ? "outline" : "cta" }), "w-full sm:w-auto")}
              >
                {status && !status.available ? t("askAlternative") : t("request")}
              </Link>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
