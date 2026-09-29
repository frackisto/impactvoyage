"use client";

import axios, { AxiosError } from "axios";

import { toApiError } from "./errors";

/**
 * Client Axios des Client Components (formulaires, recherche instantanée...).
 * Il passe par le BFF Next.js (/api/backend/...) : le navigateur n'a jamais
 * accès aux jetons, qui restent dans des cookies httpOnly.
 *
 * Chemins SANS barre finale (Next.js redirige « /x/ » vers « /x ») ; le relais
 * ajoute celle qu'attend Django : api.get("tours", { params: { travelers: 2 } }).
 */
export const api = axios.create({
  baseURL: "/api/backend",
  withCredentials: true,
  headers: { Accept: "application/json" },
});

// Langue de la page (<html lang>) plutôt que celle du navigateur : Django répond et
// écrit ses emails (confirmation de devis, de réservation…) dans la langue du site consulté.
api.interceptors.request.use((config) => {
  const lang = typeof document === "undefined" ? "" : document.documentElement.lang;
  if (lang) config.headers.set("Accept-Language", lang);
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      return Promise.reject(toApiError(error.response.status, error.response.data));
    }
    return Promise.reject(toApiError(0, null));
  },
);
