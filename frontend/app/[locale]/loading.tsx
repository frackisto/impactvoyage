import { useTranslations } from "next-intl";

import { Container } from "@/components/common/container";
import { CardGridSkeleton } from "@/components/common/states";
import { Skeleton } from "@/components/ui/skeleton";

/** Écran de chargement pendant la navigation (skeleton loaders, CdC § 4). */
export default function Loading() {
  const t = useTranslations("States");
  return (
    <>
      <div className="bg-ocean-900 py-14">
        <Container className="flex flex-col gap-3">
          <Skeleton className="h-4 w-40 bg-white/20" />
          <Skeleton className="h-10 w-2/3 bg-white/20" />
        </Container>
      </div>
      <Container className="py-12">
        <CardGridSkeleton label={t("loading")} />
      </Container>
    </>
  );
}
