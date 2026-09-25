import { cn } from "@/lib/utils";

type SectionHeadingProps = {
  title: string;
  eyebrow?: string;
  description?: string;
  align?: "start" | "center";
  as?: "h1" | "h2" | "h3";
  className?: string;
};

/** Titre de section : sur-titre orange, titre, texte d'introduction. */
export function SectionHeading({
  title,
  eyebrow,
  description,
  align = "start",
  as: Heading = "h2",
  className,
}: SectionHeadingProps) {
  return (
    <div className={cn("flex max-w-3xl flex-col gap-2", align === "center" && "mx-auto items-center text-center", className)}>
      {eyebrow && (
        <p className="text-sm font-semibold uppercase tracking-wider text-sunset-700">{eyebrow}</p>
      )}
      <Heading className="text-balance text-3xl font-bold text-ocean-900 sm:text-4xl">{title}</Heading>
      {description && <p className="text-pretty text-lg text-muted-foreground">{description}</p>}
    </div>
  );
}
