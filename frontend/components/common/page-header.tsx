import { ChevronRightIcon } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

import { Container } from "./container";

type Crumb = { label: string; href?: string };

type PageHeaderProps = {
  title: string;
  description?: string;
  breadcrumbs?: Crumb[];
};

/** Bandeau de titre des pages intérieures, avec fil d'Ariane. */
export async function PageHeader({ title, description, breadcrumbs = [] }: PageHeaderProps) {
  const t = await getTranslations("Nav");
  const crumbs: Crumb[] = [{ label: t("home"), href: "/" }, ...breadcrumbs];

  return (
    <section className="bg-gradient-to-br from-ocean-800 to-ocean-950 text-white">
      <Container className="flex flex-col gap-3 py-10 sm:py-14">
        <nav aria-label={t("breadcrumb")}>
          <ol className="flex flex-wrap items-center gap-1 text-sm text-ocean-100">
            {crumbs.map((crumb, index) => (
              <li key={crumb.label} className="flex items-center gap-1">
                {index > 0 && <ChevronRightIcon aria-hidden="true" className="size-4 rtl:rotate-180" />}
                {crumb.href && index < crumbs.length - 1 ? (
                  <Link href={crumb.href} className="hover:text-white hover:underline">
                    {crumb.label}
                  </Link>
                ) : (
                  <span aria-current={index === crumbs.length - 1 ? "page" : undefined}>{crumb.label}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
        <h1 className="text-balance text-3xl font-bold sm:text-5xl">{title}</h1>
        {description && <p className="max-w-3xl text-lg text-ocean-100">{description}</p>}
      </Container>
    </section>
  );
}
