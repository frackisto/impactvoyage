import { CalendarDaysIcon, ClockIcon, TagIcon } from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import { notFound } from "next/navigation";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { PostCard } from "@/components/blog/post-card";
import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { Section, SectionHeader } from "@/components/common/page-section";
import { RichText } from "@/components/common/rich-text";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { mediaSrc } from "@/lib/media";
import { absoluteUrl, alternates, SITE_URL } from "@/lib/seo";
import { getPost, relatedPosts } from "@/services/agency.service";
import { getSiteSettings } from "@/services/site.service";

type Props = PageProps<"/[locale]/blog/[slug]">;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();
  const image = mediaSrc(post.cover_image);
  return {
    title: post.seo_title || post.title,
    description: post.seo_description || post.excerpt,
    alternates: alternates(`/blog/${slug}`, locale),
    openGraph: {
      type: "article",
      title: post.title,
      description: post.excerpt,
      url: absoluteUrl(`/blog/${slug}`, locale),
      publishedTime: post.published_at ?? undefined,
      images: image ? [{ url: image, alt: post.cover_alt || post.title }] : undefined,
    },
  };
}

/** Article du blog (CdC § 21). */
export default async function PostPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const post = await getPost(slug);
  if (!post) notFound();

  const [t, tNav, lang, related, settings] = await Promise.all([
    getTranslations("Blog"),
    getTranslations("Nav"),
    getLocale(),
    relatedPosts(post),
    getSiteSettings(),
  ]);
  const breadcrumbs = [{ label: t("title"), href: "/blog" }, { label: post.title }];
  const image = mediaSrc(post.cover_image);
  const published = post.published_at ? formatDate(post.published_at, lang, { day: "numeric", month: "long", year: "numeric" }) : null;

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "BlogPosting",
              headline: post.title,
              description: post.excerpt,
              url: absoluteUrl(`/blog/${slug}`, locale),
              image: image ? `${SITE_URL}${image}` : undefined,
              datePublished: post.published_at,
              inLanguage: locale,
              author: post.author_name
                ? { "@type": "Person", name: post.author_name }
                : settings.agency_name ? { "@type": "Organization", name: settings.agency_name } : undefined,
              publisher: settings.agency_name ? { "@type": "TravelAgency", name: settings.agency_name, url: SITE_URL } : undefined,
              keywords: post.tags.map((tag) => tag.name).join(", ") || undefined,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/blog/${slug}`, locale),
          ],
        }}
      />
      <PageHeader title={post.title} description={post.excerpt} breadcrumbs={breadcrumbs} />

      <Container className="flex max-w-3xl flex-col gap-8 py-10 sm:py-14">
        <p className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
          {post.category && (
            <Link href={`/blog?category=${post.category.slug}`} className="font-semibold text-sunset-700 hover:underline">
              {post.category.name}
            </Link>
          )}
          {published && (
            <span className="inline-flex items-center gap-1.5">
              <CalendarDaysIcon aria-hidden="true" className="size-4 text-ocean-600" />
              {t("publishedOn", { date: published })}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5">
            <ClockIcon aria-hidden="true" className="size-4 text-ocean-600" />
            {t("readingTime", { count: post.reading_time })}
          </span>
          {post.author_name && <span>{t("by", { author: post.author_name })}</span>}
        </p>

        {image && (
          <div className="relative aspect-[16/9] overflow-hidden rounded-3xl bg-ocean-50">
            <Image src={image} alt={post.cover_alt || ""} fill priority sizes="(min-width: 768px) 768px, 100vw" className="object-cover" />
          </div>
        )}

        <article aria-label={post.title}>
          <RichText text={post.content} />
        </article>

        {post.tags.length > 0 && (
          <ul aria-label={t("tags")} className="flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <li key={tag.slug}>
                <Link
                  href={`/blog?tag=${tag.slug}`}
                  className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium text-ocean-900 hover:bg-ocean-50"
                >
                  <TagIcon aria-hidden="true" className="size-3.5" />
                  {tag.name}
                </Link>
              </li>
            ))}
          </ul>
        )}

        <aside aria-labelledby="post-cta" className="flex flex-col items-start gap-3 rounded-3xl bg-ocean-900 p-6 text-white">
          <h2 id="post-cta" className="text-2xl font-bold">
            {t("ctaTitle")}
          </h2>
          <p className="text-ocean-100">{t("ctaText")}</p>
          <Link href="/devis" className={buttonVariants({ variant: "cta" })}>
            {t("ctaQuote")}
          </Link>
        </aside>
      </Container>

      {related.length > 0 && (
        <Section tone="tint" aria-labelledby="post-related">
          <SectionHeader id="post-related" title={t("relatedTitle")} href="/blog" linkLabel={t("allPosts")} />
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((other) => (
              <li key={other.id} className="grid">
                <PostCard post={other} />
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
