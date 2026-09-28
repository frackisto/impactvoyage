import "server-only";

import { cache } from "react";

import { nullIfNotFound } from "@/lib/api/errors";
import { apiGet } from "@/lib/api/server";
import type {
  AlbumDetail,
  AlbumList,
  BlogPostDetail,
  BlogPostList,
  Category,
  OfferDetail,
  OfferList,
  Paginated,
  Service,
  TransportService,
  VisaService,
} from "@/types";

/* ---------- Prestations de l'agence (CdC § 11) ---------- */

export const listServices = cache(() => apiGet<Service[]>("services/", { tags: ["services"] }));

/* ---------- Offres promotionnelles (CdC § 17) ---------- */

export const OFFER_TYPES = ["VOYAGE", "HOTEL", "CIRCUIT", "BILLET", "LOCATION", "PACKAGE"] as const;
export type OfferFilters = { offer_type?: string; destination?: string; page?: number };
const OFFER_TAGS = ["offers"];

export function listOffers(filters: OfferFilters) {
  return apiGet<Paginated<OfferList>>("offers/", { query: { ...filters, ordering: "end_date" }, tags: OFFER_TAGS });
}

/** Types d'offre et destinations réellement présents parmi les offres en cours. */
export const offerFacets = cache(async () => {
  const page = await apiGet<Paginated<OfferDetail>>("offers/", { query: { page_size: 48 }, tags: OFFER_TAGS });
  return {
    count: page.count,
    types: OFFER_TYPES.filter((type) => page.results.some((o) => o.offer_type === type)),
  };
});

export const getOffer = cache((slug: string) =>
  nullIfNotFound(apiGet<OfferDetail>(`offers/${encodeURIComponent(slug)}/`, { tags: OFFER_TAGS })),
);

export async function relatedOffers(offer: OfferDetail) {
  const page = await listOffers({}).catch(() => null);
  return (page?.results ?? []).filter((o) => o.slug !== offer.slug).slice(0, 3);
}

/* ---------- Visas (CdC § 7, § 11) ---------- */

export const VISA_PURPOSES = ["TOURISME", "AFFAIRES", "ETUDES", "FAMILLE", "TRANSIT", "AUTRE"] as const;
export type VisaFilters = { destination_country_code?: string; purpose?: string };
const VISA_TAGS = ["visas"];

/** Toutes les formules (quelques dizaines au plus), filtrées par pays et motif. */
export function listVisas(filters: VisaFilters = {}) {
  return apiGet<Paginated<VisaService>>("visas/", { query: { ...filters, page_size: 100 }, tags: VISA_TAGS });
}

/** Formules d'un pays (/visa/france) ; null si le pays n'est pas proposé. */
export const visasForCountry = cache((slug: string) =>
  nullIfNotFound(apiGet<VisaService[]>(`visas/${encodeURIComponent(slug)}/`, { tags: VISA_TAGS })),
);

/* ---------- Transport (CdC § 7) ---------- */

export const TRANSPORT_TYPES = ["TRANSFERT_AEROPORT", "BUS", "NAVETTE", "FERRY", "TRAIN", "CHAUFFEUR"] as const;
export type TransportFilters = {
  transport_type?: string;
  origin?: string;
  destination?: string;
  passengers?: number;
  page?: number;
};

export function listTransport(filters: TransportFilters) {
  return apiGet<Paginated<TransportService>>("transport/", { query: { ...filters, ordering: "price_from" }, tags: ["transport"] });
}

/* ---------- Médiathèque (CdC § 16) ---------- */

const MEDIA_TAGS = ["media"];

export function listAlbums(filters: { category?: string; page?: number }) {
  return apiGet<Paginated<AlbumList>>("media/albums/", { query: filters, tags: MEDIA_TAGS });
}

export const getAlbum = cache((slug: string) =>
  nullIfNotFound(apiGet<AlbumDetail>(`media/albums/${encodeURIComponent(slug)}/`, { tags: MEDIA_TAGS })),
);

/* ---------- Blog (CdC § 21) ---------- */

const BLOG_TAGS = ["blog"];

export function listPosts(filters: { category?: string; tag?: string; page?: number }) {
  return apiGet<Paginated<BlogPostList>>("blog/", { query: filters, tags: BLOG_TAGS });
}

export const getPost = cache((slug: string) =>
  nullIfNotFound(apiGet<BlogPostDetail>(`blog/${encodeURIComponent(slug)}/`, { tags: BLOG_TAGS })),
);

export async function relatedPosts(post: BlogPostDetail) {
  const page = await listPosts({ category: post.category?.slug }).catch(() => null);
  const others = (page?.results ?? []).filter((p) => p.slug !== post.slug);
  if (others.length >= 3) return others.slice(0, 3);
  const latest = await listPosts({}).catch(() => null);
  const more = (latest?.results ?? []).filter((p) => p.slug !== post.slug && !others.some((o) => o.slug === p.slug));
  return [...others, ...more].slice(0, 3);
}

/** Catégories de la médiathèque ou du blog (filtres). */
export const categoriesOf = cache((kind: "MEDIA" | "BLOG") =>
  apiGet<Category[]>("categories/", { query: { kind }, tags: ["categories"] }),
);
