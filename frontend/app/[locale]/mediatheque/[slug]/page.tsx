import { PlayCircleIcon } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getLocale, getTranslations, setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/states";
import { Gallery } from "@/components/media/gallery";
import { breadcrumbList, JsonLd } from "@/components/seo/json-ld";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { formatDate } from "@/lib/format";
import { mediaSrc } from "@/lib/media";
import { absoluteUrl, alternates } from "@/lib/seo";
import { excerpt } from "@/lib/text";
import { getAlbum } from "@/services/agency.service";

type Props = PageProps<"/[locale]/mediatheque/[slug]">;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  const album = await getAlbum(slug);
  if (!album) notFound();
  const t = await getTranslations({ locale, namespace: "Media" });
  const image = mediaSrc(album.cover);
  const description = excerpt(album.description || t("albumMeta", { title: album.title }));
  return {
    title: album.title,
    description,
    alternates: alternates(`/mediatheque/${slug}`, locale),
    openGraph: { title: album.title, description, images: image ? [{ url: image, alt: album.title }] : undefined },
  };
}

/** Album de la médiathèque : photos en galerie (visionneuse plein écran) et liens vidéo. */
export default async function AlbumPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const album = await getAlbum(slug);
  if (!album) notFound();

  const [t, tNav, lang] = await Promise.all([getTranslations("Media"), getTranslations("Nav"), getLocale()]);
  const breadcrumbs = [{ label: t("title"), href: "/mediatheque" }, { label: album.title }];
  const photos = album.items.filter((item) => item.type === "PHOTO" && item.image);
  const videos = album.items.filter((item) => item.type === "VIDEO" && item.video_url);
  const date = album.published_at
    ? formatDate(`${album.published_at}T00:00:00Z`, lang, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })
    : null;

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "ImageGallery",
              name: album.title,
              description: album.description || undefined,
              url: absoluteUrl(`/mediatheque/${slug}`, locale),
              datePublished: album.published_at,
            },
            breadcrumbList([{ label: tNav("home"), href: "/" }, ...breadcrumbs], `/mediatheque/${slug}`, locale),
          ],
        }}
      />
      <PageHeader
        title={album.title}
        description={[album.description, date && t("publishedOn", { date })].filter(Boolean).join(" · ")}
        breadcrumbs={breadcrumbs}
      />
      <Container className="flex flex-col gap-10 py-10 sm:py-14">
        {photos.length > 0 ? (
          <section aria-labelledby="album-photos" className="flex flex-col gap-5">
            <h2 id="album-photos" className="text-2xl font-bold text-ocean-900">
              {t("photos", { count: photos.length })}
            </h2>
            <Gallery
              title={album.title}
              photos={photos.map((item) => ({ id: item.id, image: item.image, alt: item.alt_text || item.title || album.title }))}
            />
          </section>
        ) : (
          videos.length === 0 && <EmptyState title={t("emptyAlbum")} />
        )}

        {videos.length > 0 && (
          <section aria-labelledby="album-videos" className="flex flex-col gap-5">
            <h2 id="album-videos" className="text-2xl font-bold text-ocean-900">
              {t("videos")}
            </h2>
            {/* Lien vers la plateforme vidéo (YouTube, Vimeo) plutôt qu'un lecteur intégré. */}
            <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {videos.map((video, index) => (
                <li key={video.id}>
                  <a
                    href={video.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 rounded-2xl border bg-card p-5 font-semibold text-ocean-900 hover:border-ocean-300 hover:shadow-md"
                  >
                    <PlayCircleIcon aria-hidden="true" className="size-8 shrink-0 text-sunset-600" />
                    {video.title || video.alt_text || t("video", { number: index + 1 })}
                    <span className="sr-only">{t("newTab")}</span>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}

        <Link href="/mediatheque" className={`${buttonVariants({ variant: "outline" })} self-start`}>
          {t("backToAlbums")}
        </Link>
      </Container>
    </>
  );
}
