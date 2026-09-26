import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

type SegmentedNavProps = {
  label: string;
  items: { href: string; label: string }[];
  /** Chemin de la page courante, sans langue. */
  current: string;
};

/** Onglets de navigation entre pages sœurs (circuits nationaux / internationaux...). */
export function SegmentedNav({ label, items, current }: SegmentedNavProps) {
  return (
    <nav aria-label={label}>
      <ul className="inline-flex flex-wrap rounded-3xl border bg-ocean-50 p-1">
        {items.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={item.href === current ? "page" : undefined}
              className={cn(
                "inline-flex h-10 items-center rounded-full px-5 text-sm font-semibold transition-colors",
                item.href === current ? "bg-ocean-600 text-white" : "text-ocean-900 hover:bg-white",
              )}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
