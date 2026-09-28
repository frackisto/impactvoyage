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
export type Service = Schemas["Service"];
export type VisaService = Schemas["VisaService"];
export type EventList = Schemas["EventList"];
export type OfferList = Schemas["OfferList"];
export type Review = Schemas["Review"];
export type ResidenceList = Schemas["ResidenceList"];
export type Category = Schemas["Category"];
export type RatingSummary = Schemas["RatingSummary"];
export type TourDeparture = Schemas["TourDeparture"];
export type HotelList = Schemas["HotelList"];
export type HotelDetail = Schemas["HotelDetail"];
export type ResidenceDetail = Schemas["ResidenceDetail"];
export type Amenity = Schemas["Amenity"];
export type RoomAvailability = Schemas["RoomAvailability"];
export type Availability = Schemas["Availability"];
export type VehicleList = Schemas["VehicleList"];
export type VehicleDetail = Schemas["VehicleDetail"];
export type ActivityList = Schemas["ActivityList"];
export type ActivityDetail = Schemas["ActivityDetail"];
export type ActivityAvailability = Schemas["ActivityAvailability"];
export type EventDetail = Schemas["EventDetail"];
export type MediaAsset = Schemas["MediaAsset"];
export type SearchResponse = Schemas["SearchResponse"];
export type SearchResult = Schemas["SearchResult"];
export type QuoteClient = Schemas["QuoteClient"];
export type OfferDetail = Schemas["OfferDetail"];
export type TransportService = Schemas["TransportService"];
export type AlbumList = Schemas["AlbumList"];
export type AlbumDetail = Schemas["AlbumDetail"];
export type BlogPostList = Schemas["BlogPostList"];
export type BlogPostDetail = Schemas["BlogPostDetail"];

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
