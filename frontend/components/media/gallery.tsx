"use client";

import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { useState, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { mediaSrc } from "@/lib/media";
import { cn } from "@/lib/utils";

export type GalleryPhoto = { id: number; image: string | null; alt: string };

/**
 * Galerie photo (CdC § 8, § 18) : grille de vignettes, puis visionneuse plein
 * écran navigable au clavier (flèches gauche/droite, Échap pour fermer).
 */
export function Gallery({ photos, title }: { photos: GalleryPhoto[]; title: string }) {
  const t = useTranslations("Gallery");
  const [index, setIndex] = useState<number | null>(null);
  const items = photos.flatMap((p) => {
    const src = mediaSrc(p.image);
    return src ? [{ ...p, src }] : [];
  });
  if (!items.length) return null;

  const total = items.length;
  const current = index === null ? null : items[index];
  const go = (step: number) => setIndex((i) => (i === null ? i : (i + step + total) % total));

  function onKeyDown(event: KeyboardEvent) {
    // En arabe (RTL), « suivant » est à gauche.
    const rtl = document.documentElement.dir === "rtl";
    if (event.key === "ArrowRight") go(rtl ? -1 : 1);
    if (event.key === "ArrowLeft") go(rtl ? 1 : -1);
  }

  return (
    <>
      {/* 3 photos : la grande à gauche, les deux autres empilées à droite, sans case vide. */}
      <ul className={cn("grid grid-cols-2 gap-3 sm:grid-cols-3", total !== 3 && "lg:grid-cols-4")}>
        {items.map((photo, i) => (
          <li key={photo.id} className={cn(i === 0 && total > 2 && "col-span-2 row-span-2")}>
            <button
              type="button"
              onClick={() => setIndex(i)}
              aria-label={t("open", { index: i + 1, total, alt: photo.alt })}
              className="group relative block aspect-[4/3] size-full overflow-hidden rounded-2xl bg-ocean-50 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/60"
            >
              <Image
                src={photo.src}
                alt=""
                fill
                sizes={i === 0 && total > 2 ? "(min-width: 1024px) 50vw, 100vw" : "(min-width: 1024px) 25vw, 50vw"}
                className="object-cover transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100"
              />
            </button>
          </li>
        ))}
      </ul>

      <Dialog open={current !== null} onOpenChange={(open) => !open && setIndex(null)}>
        <DialogContent
          closeLabel={t("close")}
          onKeyDown={onKeyDown}
          className="max-w-[calc(100%-1rem)] gap-3 bg-ocean-950 p-3 text-white ring-white/10 sm:max-w-5xl sm:p-4 [&_[data-slot=dialog-close]]:text-white [&_[data-slot=dialog-close]]:hover:bg-white/10"
        >
          {current && index !== null && (
            <>
              <DialogTitle className="pe-10 text-sm font-normal text-ocean-100">
                {title} — {t("counter", { index: index + 1, total })}
              </DialogTitle>
              <div className="relative aspect-[3/2] w-full overflow-hidden rounded-lg bg-black">
                <Image src={current.src} alt={current.alt} fill sizes="(min-width: 1024px) 64rem, 100vw" className="object-contain" />
              </div>
              {total > 1 && (
                <div className="flex items-center justify-between gap-2">
                  <Button variant="inverse" size="icon" onClick={() => go(-1)} aria-label={t("previous")}>
                    <ChevronLeftIcon aria-hidden="true" className="rtl:rotate-180" />
                  </Button>
                  <p aria-live="polite" className="text-sm text-ocean-100">
                    {current.alt}
                  </p>
                  <Button variant="inverse" size="icon" onClick={() => go(1)} aria-label={t("next")}>
                    <ChevronRightIcon aria-hidden="true" className="rtl:rotate-180" />
                  </Button>
                </div>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
