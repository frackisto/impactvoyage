"use client";

import { ChevronDownIcon } from "lucide-react";
import { useTranslations } from "next-intl";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link, usePathname } from "@/i18n/navigation";
import { isActive, MAIN_NAV } from "@/lib/navigation";
import { cn } from "@/lib/utils";

const linkClass =
  "relative whitespace-nowrap rounded-md px-2 py-2 text-[0.95rem] font-semibold text-ocean-900 transition-colors hover:text-ocean-600";

/** Menu principal grand écran ; les entrées secondaires sont regroupées dans « Plus ». */
export function DesktopNav() {
  const t = useTranslations("Nav");
  const pathname = usePathname();
  const primary = MAIN_NAV.filter((item) => !item.secondary && item.href !== "/");
  const secondary = MAIN_NAV.filter((item) => item.secondary);
  const secondaryActive = secondary.some((item) => isActive(item.href, pathname));

  return (
    <nav aria-label={t("main")} className="hidden xl:block">
      <ul className="flex items-center gap-0.5">
        {primary.map((item) => {
          const active = isActive(item.href, pathname);
          return (
            <li key={item.key}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  linkClass,
                  active &&
                    "text-ocean-600 after:absolute after:inset-x-2 after:-bottom-0.5 after:h-0.5 after:rounded-full after:bg-sunset-500",
                )}
              >
                {t(item.key)}
              </Link>
            </li>
          );
        })}
        <li>
          <DropdownMenu>
            <DropdownMenuTrigger
              className={cn(linkClass, "inline-flex items-center gap-1", secondaryActive && "text-ocean-600")}
            >
              {t("more")}
              <ChevronDownIcon aria-hidden="true" className="size-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-48">
              {secondary.map((item) => (
                <DropdownMenuItem
                  key={item.key}
                  render={<Link href={item.href} />}
                  className="text-base font-medium"
                >
                  {t(item.key)}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </li>
      </ul>
    </nav>
  );
}
