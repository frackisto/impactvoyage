"use client";

import { UserRoundIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import { useSession } from "@/hooks/use-session";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

/** « Connexion » ou prénom de l'utilisateur connecté (lien vers son espace). */
export function AccountLink({ className }: { className?: string }) {
  const t = useTranslations("Header");
  const { data: user } = useSession();

  return (
    <Link
      href={user ? "/profile" : "/login"}
      className={cn("inline-flex items-center gap-1.5 text-sm font-medium hover:underline", className)}
    >
      <UserRoundIcon aria-hidden="true" className="size-4" />
      {user ? user.first_name || t("account") : t("login")}
    </Link>
  );
}
