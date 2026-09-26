import { ArrowRightIcon } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";

import { Container } from "./container";
import { SectionHeading } from "./section-heading";

/** Section de page : espacement vertical commun, fond clair ou teinté. */
export function Section({
  children,
  className,
  tone = "light",
  ...props
}: React.ComponentProps<"section"> & { tone?: "light" | "tint" }) {
  return (
    <section className={cn("py-16 sm:py-20", tone === "tint" && "bg-ocean-50/60", className)} {...props}>
      <Container className="flex flex-col gap-10">{children}</Container>
    </section>
  );
}

type SectionHeaderProps = {
  eyebrow?: string;
  title: string;
  text?: string;
  href?: string;
  linkLabel?: string;
  id?: string;
};

/** Titre de section avec, à droite, un lien « Voir tout ». */
export function SectionHeader({ eyebrow, title, text, href, linkLabel, id }: SectionHeaderProps) {
  return (
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <SectionHeading eyebrow={eyebrow} title={title} description={text} id={id} />
      {href && linkLabel && (
        <Link href={href} className={cn(buttonVariants({ variant: "outline" }), "shrink-0")}>
          {linkLabel}
          <ArrowRightIcon aria-hidden="true" data-icon="inline-end" className="rtl:rotate-180" />
        </Link>
      )}
    </div>
  );
}
