import { getTranslations } from "next-intl/server";

import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";

export default async function NotFound() {
  const t = await getTranslations("Errors");
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-4 px-4 py-24 text-center">
      <p className="font-heading text-6xl font-bold text-ocean-200">404</p>
      <h1 className="text-3xl font-bold text-ocean-800">{t("notFoundTitle")}</h1>
      <p className="text-muted-foreground">{t("notFoundText")}</p>
      <Link href="/" className={buttonVariants({ size: "lg" })}>
        {t("backHome")}
      </Link>
    </div>
  );
}
