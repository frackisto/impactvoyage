"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { polyfillCountryFlagEmojis } from "country-flag-emoji-polyfill";
import { useEffect, useState, type ReactNode } from "react";
import { z } from "zod";

// zod 4 compile ses validations avec new Function() quand eval est permis : la CSP du
// site l'interdit (Phase 23). Mode sans compilation, pour ne pas déclencher de violation.
z.config({ jitless: true });

/** Fournisseurs côté client : cache TanStack Query (recherche, pagination, formulaires). */
export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 60_000, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );
  useEffect(() => {
    // Chrome et Edge sous Windows n'affichent pas les drapeaux emoji (« CI » au lieu de 🇨🇮) :
    // la police Twemoji (77 ko, auto-hébergée) n'est chargée que dans ce cas.
    polyfillCountryFlagEmojis("Twemoji Country Flags", "/fonts/TwemojiCountryFlags.woff2");
  }, []);
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
