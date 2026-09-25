import { CompassIcon, TriangleAlertIcon, type LucideIcon } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type StateProps = {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
};

/** État vide (« aucun résultat », CdC § 4 et § 7). */
export function EmptyState({ title, description, icon: Icon = CompassIcon, action, className }: StateProps) {
  return (
    <div className={cn("flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-ocean-50/50 px-6 py-12 text-center", className)}>
      <span className="flex size-14 items-center justify-center rounded-full bg-ocean-100 text-ocean-700">
        <Icon aria-hidden="true" className="size-7" />
      </span>
      <h3 className="text-xl font-semibold text-ocean-900">{title}</h3>
      {description && <p className="max-w-md text-muted-foreground">{description}</p>}
      {action}
    </div>
  );
}

/** Message d'erreur annoncé aux lecteurs d'écran (role="alert"). */
export function ErrorState({ title, description, icon: Icon = TriangleAlertIcon, action, className }: StateProps) {
  return (
    <div role="alert" className={cn("flex flex-col items-center gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 px-6 py-12 text-center", className)}>
      <Icon aria-hidden="true" className="size-8 text-destructive" />
      <h3 className="text-xl font-semibold text-ocean-900">{title}</h3>
      {description && <p className="max-w-md text-muted-foreground">{description}</p>}
      {action}
    </div>
  );
}

/** Squelette d'une carte de contenu, pendant le chargement. */
export function ContentCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl border bg-card" aria-hidden="true">
      <Skeleton className="aspect-[4/3] w-full rounded-none" />
      <div className="flex flex-col gap-3 p-4">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-6 w-1/4" />
      </div>
    </div>
  );
}

export function CardGridSkeleton({ count = 6, label }: { count?: number; label: string }) {
  return (
    <div role="status" aria-live="polite" className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <span className="sr-only">{label}</span>
      {Array.from({ length: count }, (_, i) => (
        <ContentCardSkeleton key={i} />
      ))}
    </div>
  );
}
