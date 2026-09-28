import { NewspaperIcon, XIcon } from "lucide-react";
import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { PostCard } from "@/components/blog/post-card";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Pagination } from "@/components/common/pagination";
import { SegmentedNav } from "@/components/common/segmented-nav";
import { EmptyState, ErrorState } from "@/components/common/states";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { pageParam, param, type SearchParams } from "@/lib/search-params";
import { alternates } from "@/lib/seo";
import { categoriesOf, getPost, listPosts } from "@/services/agency.service";
import type { BlogPostList, Category, Paginated } from "@/types";

const PATH = "/blog";
const PAGE_SIZE = 12;

function parseFilters(params: SearchParams) {
  const slug = (key: string) => {
    const value = param(params, key);
    return value && /^[\w-]{1,120}$/.test(value) ? value : undefined;
  };
  return { category: slug("category"), tag: slug("tag"), page: pageParam(params) };
}

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/blog">): Promise<Metadata> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const t = await getTranslations({ locale, namespace: "Blog" });
  const filters = parseFilters(query);
  return {
    title: t("title"),
    description: t("metaDescription"),
    alternates: alternates(PATH, locale),
    robots: filters.category || filters.tag || filters.page > 1 ? { index: false, follow: true } : undefined,
  };
}

/** Blog / conseils voyage (CdC § 21), filtrable par catégorie ou mot-clé. */
export default async function BlogPage({ params, searchParams }: PageProps<"/[locale]/blog">) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  setRequestLocale(locale);
  const t = await getTranslations("Blog");
  const filters = parseFilters(query);

  let posts: Paginated<BlogPostList> | null = null;
  let categories: Category[] = [];
  try {
    [posts, categories] = await Promise.all([listPosts(filters), categoriesOf("BLOG").catch(() => [])]);
  } catch {
    posts = null;
  }
  const categoryHref = (slug?: string) => (slug ? `${PATH}?category=${slug}` : PATH);
  // Nom affiché du mot-clé (pas d'API des mots-clés) : repris du premier article concerné.
  const first = filters.tag ? posts?.results[0] : undefined;
  const tagName = first ? ((await getPost(first.slug))?.tags.find((tag) => tag.slug === filters.tag)?.name ?? filters.tag) : filters.tag;

  return (
    <>
      <PageHeader title={t("title")} description={t("intro")} breadcrumbs={[{ label: t("title") }]} />
      <Container className="flex flex-col gap-8 py-10 sm:py-14">
        {categories.length > 1 && !filters.tag && (
          <SegmentedNav
            label={t("categories")}
            current={categoryHref(filters.category)}
            items={[{ href: PATH, label: t("all") }, ...categories.map((c) => ({ href: categoryHref(c.slug), label: c.name }))]}
          />
        )}
        {filters.tag && (
          <p className="flex flex-wrap items-center gap-3 text-ocean-950">
            {t("taggedWith", { tag: tagName ?? "" })}
            <Link href={PATH} className={buttonVariants({ variant: "ghost", size: "sm" })}>
              <XIcon aria-hidden="true" data-icon="inline-start" />
              {t("allPosts")}
            </Link>
          </p>
        )}
        {posts === null ? (
          <ErrorState title={t("errorTitle")} description={t("errorText")} />
        ) : posts.count > 0 ? (
          <section aria-labelledby="blog-posts" className="flex flex-col gap-6">
            <h2 id="blog-posts" className="text-lg font-semibold text-ocean-900">
              {t("results", { count: posts.count })}
            </h2>
            <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {posts.results.map((post, index) => (
                <li key={post.id} className="grid">
                  <PostCard post={post} priority={index < 2} />
                </li>
              ))}
            </ul>
            <Pagination page={filters.page} count={posts.count} pageSize={PAGE_SIZE} pathname={PATH} query={{ category: filters.category, tag: filters.tag }} />
          </section>
        ) : (
          <EmptyState
            icon={NewspaperIcon}
            title={t("emptyTitle")}
            description={t("emptyText")}
            action={
              <Link href={PATH} className={buttonVariants({ variant: "outline" })}>
                {t("allPosts")}
              </Link>
            }
          />
        )}
      </Container>
    </>
  );
}
