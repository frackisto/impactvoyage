import { getTranslations } from "next-intl/server";

/** Pied de page provisoire ; version complète (coordonnées, réseaux, liens) en Phase 9. */
export async function SiteFooter() {
  const t = await getTranslations();
  return (
    <footer className="bg-ocean-950 text-ocean-50">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-2 px-4 py-8 text-center">
        <p className="font-script text-2xl text-sunset-400">{t("Brand.slogan")}</p>
        <p className="text-sm text-ocean-200">
          © {new Date().getFullYear()} {t("Brand.name")}. {t("Footer.rights")}
        </p>
      </div>
    </footer>
  );
}
