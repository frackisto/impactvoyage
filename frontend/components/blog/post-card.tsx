import { CalendarDaysIcon, ClockIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { ContentCard } from "@/components/common/content-card";
import { formatDate } from "@/lib/format";
import type { BlogPostList } from "@/types";

/** Carte d'article du blog (CdC § 21) : catégorie, résumé, date et temps de lecture. */
export function PostCard({ post, priority }: { post: BlogPostList; priority?: boolean }) {
  const t = useTranslations("Blog");
  const locale = useLocale();
  return (
    <ContentCard
      href={`/blog/${post.slug}`}
      title={post.title}
      eyebrow={post.category?.name}
      description={post.excerpt}
      image={post.cover_image}
      imageAlt={post.cover_alt || ""}
      priority={priority}
      meta={
        <>
          {post.published_at && (
            <span className="inline-flex items-center gap-1.5">
              <CalendarDaysIcon aria-hidden="true" className="size-4 text-ocean-600" />
              {formatDate(post.published_at, locale, { day: "numeric", month: "long", year: "numeric" })}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5">
            <ClockIcon aria-hidden="true" className="size-4 text-ocean-600" />
            {t("readingTime", { count: post.reading_time })}
          </span>
        </>
      }
    />
  );
}
