"use client";

import { MailIcon, MenuIcon, PhoneIcon } from "lucide-react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { buttonVariants } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Link, usePathname } from "@/i18n/navigation";
import { isActive, MAIN_NAV } from "@/lib/navigation";
import { cn } from "@/lib/utils";

import { AccountLink } from "./account-link";
import { CurrencySwitcher } from "./currency-switcher";
import { LocaleSwitcher } from "./locale-switcher";

type MobileNavProps = { phone?: string; email?: string; currency: string };

/** Menu mobile et tablette (CdC § 34) : panneau latéral, focus piégé, fermeture au choix d'un lien. */
export function MobileNav({ phone, email, currency }: MobileNavProps) {
  const t = useTranslations();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        className={cn(buttonVariants({ variant: "ghost", size: "icon" }), "xl:hidden")}
        aria-label={t("Header.openMenu")}
      >
        <MenuIcon aria-hidden="true" className="size-6" />
      </SheetTrigger>
      <SheetContent side="right" closeLabel={t("Header.closeMenu")} className="w-[88%] gap-0 overflow-y-auto p-0 sm:max-w-sm">
        <div className="flex items-center gap-2 border-b p-4 pe-14">
          <Image src="/brand/emblem.png" alt="" width={44} height={44} className="size-11" />
          <div>
            <SheetTitle className="font-heading text-lg text-ocean-700">Impact Voyage</SheetTitle>
            <SheetDescription className="font-script text-base text-sunset-700">
              {t("Brand.slogan")}
            </SheetDescription>
          </div>
        </div>

        <nav aria-label={t("Nav.main")} className="p-2">
          <ul className="flex flex-col">
            {MAIN_NAV.map((item) => {
              const active = isActive(item.href, pathname);
              return (
                <li key={item.key}>
                  <Link
                    href={item.href}
                    onClick={close}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex min-h-12 items-center rounded-lg px-3 text-base font-semibold text-ocean-900 hover:bg-ocean-50",
                      active && "bg-ocean-50 text-ocean-700 shadow-[inset_3px_0_0_var(--color-sunset-500)]",
                    )}
                  >
                    {t(`Nav.${item.key}`)}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="flex flex-col gap-4 border-t p-4">
          <Link href="/devis" onClick={close} className={cn(buttonVariants({ variant: "cta", size: "lg" }), "w-full")}>
            {t("Nav.quote")}
          </Link>
          <AccountLink className="text-ocean-900" />
          <div className="flex flex-wrap items-center gap-3">
            <LocaleSwitcher />
            <CurrencySwitcher value={currency} />
          </div>
          {(phone || email) && (
            <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
              {phone && (
                <li>
                  <a href={`tel:${phone.replace(/\s/g, "")}`} className="inline-flex items-center gap-2 hover:text-ocean-700">
                    <PhoneIcon aria-hidden="true" className="size-4" /> {phone}
                  </a>
                </li>
              )}
              {email && (
                <li>
                  <a href={`mailto:${email}`} className="inline-flex items-center gap-2 hover:text-ocean-700">
                    <MailIcon aria-hidden="true" className="size-4" /> {email}
                  </a>
                </li>
              )}
            </ul>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
