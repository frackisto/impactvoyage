import { describe, expect, it } from "vitest";

import { pageMetadata, SITE_URL } from "./seo";

describe("pageMetadata", () => {
  it("donne canonique, hreflang, Open Graph et Twitter Card complets", () => {
    const meta = pageMetadata({
      locale: "en",
      path: "/circuits/dubai",
      title: "Dubai",
      description: "Six days in Dubai.",
      image: "/media/tours/dubai.jpg",
    });
    expect(meta.title).toBe("Dubai");
    expect(meta.alternates).toEqual({
      canonical: "/en/circuits/dubai",
      languages: { fr: "/circuits/dubai", en: "/en/circuits/dubai", "x-default": "/circuits/dubai" },
    });
    expect(meta.robots).toBeUndefined();
    expect(meta.openGraph).toMatchObject({
      type: "website",
      siteName: "Impact Voyage",
      locale: "en_US",
      alternateLocale: ["fr_FR"],
      url: `${SITE_URL}/en/circuits/dubai`,
      images: [{ url: "/media/tours/dubai.jpg", alt: "Dubai" }],
    });
    expect(meta.twitter).toMatchObject({ card: "summary_large_image", images: ["/media/tours/dubai.jpg"] });
  });

  it("utilise l'image de partage par défaut et peut exclure la page de l'index", () => {
    const meta = pageMetadata({ locale: "fr", path: "/hotels", title: "Hôtels", noindex: true });
    expect(meta.robots).toEqual({ index: false, follow: true });
    expect(meta.openGraph?.images).toEqual([
      expect.objectContaining({ url: "/brand/og-default.jpg", width: 1200, height: 630 }),
    ]);
  });

  it("titre complet pour l'accueil, date de publication pour un article", () => {
    expect(pageMetadata({ locale: "fr", path: "/", title: "Impact Voyage", absoluteTitle: true }).title)
      .toEqual({ absolute: "Impact Voyage" });
    const article = pageMetadata({
      locale: "fr", path: "/blog/visa", title: "Visa", type: "article", publishedTime: "2026-09-01T08:00:00Z",
    });
    expect(article.openGraph).toMatchObject({ type: "article", publishedTime: "2026-09-01T08:00:00Z" });
  });
});
