"use client";

import { CalendarSearchIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState, useTransition, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "@/i18n/navigation";
import { pageHref } from "@/lib/pagination";
import type { Stay } from "@/lib/stay";

const addDays = (date: string, days: number) => {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};

/**
 * Dates de séjour (et voyageurs / chambres pour un hôtel) sur une fiche : la
 * page est rendue à nouveau côté serveur avec les disponibilités de la période.
 */
export function StayForm({ pathname, current, withRooms = false }: { pathname: string; current: Stay; withRooms?: boolean }) {
  const t = useTranslations("Stays");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [start, setStart] = useState(current.start ?? "");
  const id = useId();
  const today = new Date().toISOString().slice(0, 10);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const value = (key: string) => String(data.get(key) ?? "").trim() || undefined;
    const rooms = value("rooms");
    startTransition(() =>
      router.replace(
        pageHref(pathname, {
          start: value("start"),
          end: value("end"),
          travelers: value("travelers"),
          rooms: rooms === "1" ? undefined : rooms,
        }, 1),
        { scroll: false },
      ),
    );
  }

  return (
    <form
      onSubmit={submit}
      aria-label={t("checkLabel")}
      aria-busy={pending}
      className={`grid items-end gap-4 rounded-2xl border bg-ocean-50/70 p-5 sm:grid-cols-2 ${withRooms ? "lg:grid-cols-[1fr_1fr_8rem_8rem_auto]" : "lg:grid-cols-[1fr_1fr_auto]"}`}
    >
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-start`} className="text-sm font-semibold text-ocean-900">
          {t("arrival")}
        </label>
        <Input
          id={`${id}-start`}
          name="start"
          type="date"
          required
          min={today}
          value={start}
          onChange={(event) => setStart(event.currentTarget.value)}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-end`} className="text-sm font-semibold text-ocean-900">
          {t("departure")}
        </label>
        <Input
          id={`${id}-end`}
          name="end"
          type="date"
          required
          min={start ? addDays(start, 1) : today}
          defaultValue={current.end}
        />
      </div>
      {withRooms && (
        <>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${id}-travelers`} className="text-sm font-semibold text-ocean-900">
              {t("travelers")}
            </label>
            <Input id={`${id}-travelers`} name="travelers" type="number" min={1} max={20} inputMode="numeric" defaultValue={current.travelers} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${id}-rooms`} className="text-sm font-semibold text-ocean-900">
              {t("rooms")}
            </label>
            <Input id={`${id}-rooms`} name="rooms" type="number" min={1} max={10} inputMode="numeric" defaultValue={current.rooms ?? 1} />
          </div>
        </>
      )}
      <Button type="submit" size="lg" disabled={pending}>
        <CalendarSearchIcon aria-hidden="true" data-icon="inline-start" />
        {t("check")}
      </Button>
    </form>
  );
}
