import { ImageIcon } from "lucide-react";
import Image from "next/image";

import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

type ContentCardProps = {
  href: string;
  title: string;
  image?: string | null;
  imageAlt?: string;
  /** Petit texte au-dessus du titre (destination, catégorie...). */
  eyebrow?: string;
  description?: string | null;
  /** Badges posés sur la photo (offre, type de circuit...). */
  badges?: React.ReactNode;
  /** Infos secondaires (durée, note, places...). */
  meta?: React.ReactNode;
  /** Prix ou appel à l'action, aligné en bas de carte. */
  footer?: React.ReactNode;
  /** Charge l'image en priorité (première carte visible : meilleur LCP). */
  priority?: boolean;
  className?: string;
};

/**
 * Carte de contenu générique (circuits, destinations, hôtels, véhicules...) :
 * photo grand format, effet au survol, toute la carte est cliquable (un seul
 * lien, accessible au clavier).
 */
export function ContentCard({
  href,
  title,
  image,
  imageAlt = "",
  eyebrow,
  description,
  badges,
  meta,
  footer,
  priority,
  className,
}: ContentCardProps) {
  return (
    <article
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border bg-card shadow-sm transition-all duration-300",
        "hover:-translate-y-1 hover:shadow-xl hover:shadow-ocean-900/10 focus-within:ring-2 focus-within:ring-ring",
        "motion-reduce:transition-none motion-reduce:hover:translate-y-0",
        className,
      )}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-ocean-50">
        {image ? (
          <Image
            src={image}
            alt={imageAlt}
            fill
            priority={priority}
            sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
            className="object-cover transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100"
          />
        ) : (
          <div className="flex size-full items-center justify-center text-ocean-300">
            <ImageIcon aria-hidden="true" className="size-12" />
          </div>
        )}
        {badges && <div className="absolute start-3 top-3 flex flex-wrap gap-1.5">{badges}</div>}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        {eyebrow && <p className="text-sm font-medium text-ocean-700">{eyebrow}</p>}
        <h3 className="text-lg font-semibold leading-snug text-ocean-950">
          <Link href={href} className="after:absolute after:inset-0 focus-visible:outline-none">
            {title}
          </Link>
        </h3>
        {description && <p className="line-clamp-2 text-sm text-muted-foreground">{description}</p>}
        {meta && <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">{meta}</div>}
        {footer && <div className="mt-auto flex items-end justify-between gap-2 pt-2">{footer}</div>}
      </div>
    </article>
  );
}
