"use client";

import { CalendarSearchIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useTransition, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "@/i18n/navigation";
import { pageHref } from "@/lib/pagination";
import { today } from "@/lib/stay";

/**
 * Date et nombre de participants sur la fiche d'une activité : la page est rendue
 * à nouveau côté serveur avec les places restantes ce jour-là.
 */
export function DateForm({ pathname, date, participants, maxParticipants }: {
  pathname: string;
  date?: string;
  participants?: number;
  maxParticipants?: number | null;
}) {
  const t = useTranslations("Activities");
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const id = useId();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const value = (key: string) => String(data.get(key) ?? "").trim() || undefined;
    const count = value("participants");
    startTransition(() =>
      router.replace(pageHref(pathname, { date: value("date"), participants: count === "1" ? undefined : count }, 1), {
        scroll: false,
      }),
    );
  }

  return (
    <form
      onSubmit={submit}
      aria-label={t("checkLabel")}
      aria-busy={pending}
      className="grid items-end gap-4 rounded-2xl border bg-ocean-50/70 p-5 sm:grid-cols-[1fr_10rem_auto]"
    >
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-date`} className="text-sm font-semibold text-ocean-900">
          {t("date")}
        </label>
        <Input id={`${id}-date`} name="date" type="date" required min={today()} defaultValue={date} />
      </div>
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-participants`} className="text-sm font-semibold text-ocean-900">
          {t("participantsLabel")}
        </label>
        <Input
          id={`${id}-participants`}
          name="participants"
          type="number"
          min={1}
          max={maxParticipants ?? 50}
          inputMode="numeric"
          defaultValue={participants ?? 1}
        />
      </div>
      <Button type="submit" size="lg" disabled={pending}>
        <CalendarSearchIcon aria-hidden="true" data-icon="inline-start" />
        {t("check")}
      </Button>
    </form>
  );
}
