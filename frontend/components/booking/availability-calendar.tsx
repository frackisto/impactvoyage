import { getLocale, getTranslations } from "next-intl/server";

import { inPeriods, monthWeeks } from "@/lib/calendar";
import { intlLocale } from "@/lib/format";
import { cn } from "@/lib/utils";

type AvailabilityCalendarProps = {
  /** Périodes réservées [début, fin) au format AAAA-MM-JJ. */
  booked: string[][];
  /** Premier jour affiché (aujourd'hui), AAAA-MM-JJ. */
  from: string;
  months?: number;
};

/**
 * Calendrier de disponibilité (CdC § 12) : jours réservés barrés, jours passés
 * estompés. Un tableau par mois, lisible par les lecteurs d'écran.
 */
export async function AvailabilityCalendar({ booked, from, months = 2 }: AvailabilityCalendarProps) {
  const [t, locale] = await Promise.all([getTranslations("Availability"), getLocale()]);
  const lang = intlLocale(locale);
  const isBooked = (day: string) => inPeriods(day, booked);
  const monthTitle = new Intl.DateTimeFormat(lang, { month: "long", year: "numeric", timeZone: "UTC" });
  const dayLabel = new Intl.DateTimeFormat(lang, { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });
  // Lundi 1er janvier 2024 : sert à nommer les jours de la semaine.
  const weekdays = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(Date.UTC(2024, 0, 1 + i));
    return {
      short: new Intl.DateTimeFormat(lang, { weekday: "narrow", timeZone: "UTC" }).format(date),
      long: new Intl.DateTimeFormat(lang, { weekday: "long", timeZone: "UTC" }).format(date),
    };
  });

  const grids = Array.from({ length: months }, (_, index) => {
    const { first, weeks } = monthWeeks(from, index);
    return { key: first.toISOString(), title: monthTitle.format(first), weeks };
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-6 sm:grid-cols-2">
        {grids.map((grid) => (
          <table key={grid.key} className="w-full table-fixed border-separate border-spacing-1 text-center text-sm">
            <caption className="pb-2 text-start font-semibold capitalize text-ocean-900">{grid.title}</caption>
            <thead>
              <tr>
                {weekdays.map((day) => (
                  <th key={day.long} scope="col" abbr={day.long} className="pb-1 text-xs font-medium uppercase text-muted-foreground">
                    {day.short}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.weeks.map((week, w) => (
                <tr key={w}>
                  {week.map((day, d) => {
                    if (!day) return <td key={d} />;
                    const past = day < from;
                    const taken = !past && isBooked(day);
                    return (
                      <td
                        key={day}
                        className={cn(
                          "h-9 rounded-md tabular-nums",
                          past && "text-muted-foreground",
                          taken && "bg-rose-100 font-semibold text-rose-800 line-through",
                          !past && !taken && "bg-emerald-50 text-emerald-900",
                          day === from && "ring-2 ring-ocean-500",
                        )}
                      >
                        <span aria-hidden="true">{Number(day.slice(8))}</span>
                        <span className="sr-only">
                          {dayLabel.format(new Date(`${day}T00:00:00Z`))}
                          {past ? ` : ${t("dayPast")}` : taken ? ` : ${t("dayBooked")}` : ` : ${t("dayFree")}`}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        ))}
      </div>
      <ul className="flex flex-wrap gap-4 text-sm text-ocean-950">
        <li className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="size-4 rounded bg-emerald-50 ring-1 ring-emerald-200" /> {t("legendFree")}
        </li>
        <li className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="size-4 rounded bg-rose-100 ring-1 ring-rose-200" /> {t("legendBooked")}
        </li>
      </ul>
    </div>
  );
}
