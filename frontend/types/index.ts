/**
 * Raccourcis vers les types générés depuis le schéma OpenAPI du backend
 * (`npm run api:types` régénère types/api.d.ts — ne jamais l'éditer à la main).
 */
import type { components } from "./api";

export type Schemas = components["schemas"];

export type Money = Schemas["Money"];
export type User = Schemas["User"];
export type SiteSettings = Schemas["SiteSettings"];
export type TourList = Schemas["TourList"];
export type TourDetail = Schemas["TourDetail"];
export type DestinationList = Schemas["DestinationList"];
export type DestinationDetail = Schemas["DestinationDetail"];
export type Booking = Schemas["Booking"];

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
