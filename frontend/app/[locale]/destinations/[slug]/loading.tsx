import { useTranslations } from "next-intl";

import { Container } from "@/components/common/container";
import { Skeleton } from "@/components/ui/skeleton";

/** Chargement d'une fiche destination : hero, texte et encadré (skeleton loaders, CdC § 4). */
export default function Loading() {
  const t = useTranslations("States");
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">{t("loading")}</span>
      <div className="bg-ocean-900 py-10">
        <Container className="flex min-h-[22rem] flex-col justify-end gap-4 sm:min-h-[28rem]">
          <Skeleton className="h-6 w-48 bg-white/20" />
          <Skeleton className="h-14 w-2/3 bg-white/20" />
          <Skeleton className="h-6 w-1/2 bg-white/20" />
        </Container>
      </div>
      <Container className="grid gap-10 py-12 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="flex flex-col gap-4">
          <Skeleton className="h-9 w-1/2" />
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-5 w-full" />
          ))}
        </div>
        <Skeleton className="h-80 w-full rounded-3xl" />
      </Container>
    </div>
  );
}
