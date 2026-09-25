"use client";

import { useQuery } from "@tanstack/react-query";

import type { User } from "@/types";

/** Utilisateur connecté (null sinon), via le BFF qui rafraîchit le jeton au besoin. */
export function useSession() {
  return useQuery({
    queryKey: ["session"],
    queryFn: async (): Promise<User | null> => {
      const response = await fetch("/api/auth/session", { credentials: "same-origin" });
      if (!response.ok) return null;
      const body = (await response.json()) as { user: User | null };
      return body.user;
    },
    staleTime: 5 * 60_000,
  });
}
