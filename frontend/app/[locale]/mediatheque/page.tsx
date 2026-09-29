import { CalendarDaysIcon, ImagesIcon } from "lucide-react";
import type { Metadata } from "next";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { ContentCard } from "@/components/common/content-card";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { SegmentedNav } from "@/components/common/segmented-nav";
import { EmptyState, ErrorState } from "@/components/common/states";
import { formatDate } from "@/lib/format";
import { pageParam, param, type SearchParams } from "@/lib/search-params";
import { pageMetadata } from "@/lib/seo";
import { categoriesOf, listAlbums } from "@/services/agency.service";
import type { AlbumList, Category, Paginated } from "@/types";

const PATH = "/mediatheque";
const PAGE_SIZE = 12;

function parseFilters(params: SearchParams) {
  const category = param(params, "category");
  return { category: category && /^[\w-]{1,120}$/.test(category) ? category : undefined, page: pageParam(params) };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/mediatheque">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Media" });
  const filters = parseFilters(query);
  return pageMetadata({
    locale,
    path: PATH,
    title: t("title"),
    description: t("metaDescription"),
    noindex: Boolean(filters.category || filters.page > 1),
  });
}

/** Médiathèque (CdC § 16) : albums photo des voyages et événements de l'agence. */
export default async function MediaPage({ params, searchParams }: PageProps<"/[locale]/mediatheque">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const [t, lang] = await Promise.all([getTranslations("Media"), getLocale()]);
  const filters = parseFilters(query);

  let albums: Paginated<AlbumList> | null = null;
  let categories: Category[] = [];
  try {
    [albums, categories] = await Promise.all([listAlbums(filters), categoriesOf("MEDIA").catch(() => [])]);
  } catch {
    albums = null;
  }
  const categoryHref = (slug?: string) => (slug ? `${PATH}?category=${slug}` : PATH);

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {categories.length > 1 && (
          <SegmentedNav
            label={t("categories")}
            current={categoryHref(filters.category)}
            items={[{ href: PATH, label: t("all") }, ...categories.map((c) => ({ href: categoryHref(c.slug), label: c.name }))]}
          />
        )}
        {albums === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : albums.count > 0 ? (
          <section aria-labelledby="media-albums" className="flex flex-col gap-6">
            <h2 id="media-albums" className="text-lg font-semibold text-ocean-900">
              {t("results", { count: albums.count })}
            </h2>
            <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {albums.results.map((album, index) => (
                <li key={album.id} className="grid">
                  <ContentCard
                    href={`${PATH}/${album.slug}`}
                    title={album.title}
                    image={album.cover}
                    eyebrow={album.category?.name}
                    priority={index < 2}
                    meta={
                      <>
                        <span className="inline-flex items-center gap-1.5">
                          <ImagesIcon aria-hidden="true" className="size-4 text-ocean-600" />
                          {t("items", { count: album.items_count })}
                        </span>
                        {album.published_at && (
                          <span className="inline-flex items-center gap-1.5">
                            <CalendarDaysIcon aria-hidden="true" className="size-4 text-ocean-600" />
                            {formatDate(`${album.published_at}T00:00:00Z`, lang, { month: "long", year: "numeric", timeZone: "UTC" })}
                          </span>
                        )}
                      </>
                    }
                  />
                </li>
              ))}
            </ul>
            <Pagination page={filters.page} count={albums.count} pageSize={PAGE_SIZE} pathname={PATH} query={{ category: filters.category }} />
          </section>
        ) : (
          <EmptyState icon={ImagesIcon} title={t("emptyTitle")} description={t("emptyText")} />
        )}
      </Container>
    </>
  );
}
