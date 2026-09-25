import { cn } from "@/lib/utils";

/** Largeur maximale et marges latérales communes à toutes les sections. */
export function Container({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("mx-auto w-full max-w-7xl px-4 sm:px-6", className)} {...props} />;
}
