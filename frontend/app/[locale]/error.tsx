"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations("Errors");
  return (
    <div role="alert" className="mx-auto flex max-w-xl flex-col items-center gap-4 px-4 py-24 text-center">
      <h1 className="text-3xl font-bold text-ocean-800">{t("errorTitle")}</h1>
      <p className="text-muted-foreground">{t("errorText")}</p>
      <Button size="lg" onClick={() => reset()}>
        {t("retry")}
      </Button>
    </div>
  );
}
