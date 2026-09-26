"use client";

import { SlidersHorizontalIcon, XIcon } from "lucide-react";
import { useId, useState, useTransition, type FormEvent, type ReactNode } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useRouter } from "@/i18n/navigation";
import { pageHref } from "@/lib/pagination";
import { cn } from "@/lib/utils";

export const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm";

type Option = { value: string; label: string };

/** Description d'un champ de filtre ; `name` est le nom du paramètre d'URL (et de l'API). */
export type FilterField =
  | { type: "select"; name: string; label: string; anyLabel: string; options: Option[] }
  | { type: "date"; name: string; label: string }
  | { type: "number"; name: string; label: string; min?: number; max?: number; step?: number }
  /** Cases à cocher : valeurs jointes par des virgules (?amenities=1,4). */
  | { type: "checkboxes"; name: string; label: string; options: Option[] };

export type FilterValues = Record<string, string | undefined>;

type FilterPanelProps = {
  /** Chemin de la liste, sans langue. */
  pathname: string;
  fields: FilterField[];
  current: FilterValues;
  /** Paramètres conservés hors formulaire (tri). */
  keep?: FilterValues;
  labels: { title: string; formLabel: string; apply: string; reset: string };
};

function Labelled({ label, children }: { label: string; children: (id: string) => ReactNode }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-ocean-900">
        {label}
      </label>
      {children(id)}
    </div>
  );
}

/**
 * Panneau de filtres des listes (circuits, hébergements...) : replié sur mobile,
 * en colonne sur grand écran. Les listes déroulantes et les cases s'appliquent
 * dès qu'on les change ; les champs libres avec le bouton. Les filtres vivent
 * dans l'URL (partageable, rendu serveur).
 */
export function FilterPanel({ pathname, fields, current, keep = {}, labels }: FilterPanelProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const today = new Date().toISOString().slice(0, 10);
  const active = fields.filter((field) => current[field.name]).length;

  function submit(form: HTMLFormElement) {
    const values: FilterValues = { ...keep };
    const data = new FormData(form);
    for (const field of fields) {
      const raw = field.type === "checkboxes" ? data.getAll(field.name).join(",") : data.get(field.name);
      const value = typeof raw === "string" ? raw.trim() : "";
      values[field.name] = value || undefined;
    }
    startTransition(() => router.push(pageHref(pathname, values, 1), { scroll: false }));
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submit(event.currentTarget);
  };
  const autoSubmit = (event: { currentTarget: HTMLInputElement | HTMLSelectElement }) => {
    if (event.currentTarget.form) submit(event.currentTarget.form);
  };

  return (
    <div className="flex flex-col gap-3" aria-busy={pending}>
      <Button
        type="button"
        variant="outline"
        size="lg"
        className="w-full justify-between lg:hidden"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="inline-flex items-center gap-2">
          <SlidersHorizontalIcon aria-hidden="true" />
          {labels.title}
        </span>
        {active > 0 && <span className="rounded-full bg-ocean-600 px-2 text-xs text-white">{active}</span>}
      </Button>

      <form
        id={panelId}
        onSubmit={onSubmit}
        role="search"
        aria-label={labels.formLabel}
        // key : le formulaire reprend les valeurs de l'URL après chaque navigation.
        key={JSON.stringify(current)}
        className={cn("flex-col gap-4 rounded-2xl border bg-card p-5", open ? "flex" : "hidden lg:flex")}
      >
        <h2 className="hidden text-lg font-bold text-ocean-900 lg:block">{labels.title}</h2>
        {fields.map((field) => {
          const value = current[field.name];
          switch (field.type) {
            case "select":
              return field.options.length > 0 ? (
                <Labelled key={field.name} label={field.label}>
                  {(id) => (
                    <select id={id} name={field.name} defaultValue={value ?? ""} className={selectClass} onChange={autoSubmit}>
                      <option value="">{field.anyLabel}</option>
                      {field.options.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  )}
                </Labelled>
              ) : null;
            case "date":
              return (
                <Labelled key={field.name} label={field.label}>
                  {(id) => <Input id={id} name={field.name} type="date" min={today} defaultValue={value} />}
                </Labelled>
              );
            case "number":
              return (
                <Labelled key={field.name} label={field.label}>
                  {(id) => (
                    <Input
                      id={id}
                      name={field.name}
                      type="number"
                      inputMode="numeric"
                      min={field.min}
                      max={field.max}
                      step={field.step}
                      defaultValue={value}
                    />
                  )}
                </Labelled>
              );
            case "checkboxes": {
              if (!field.options.length) return null;
              const checked = new Set((value ?? "").split(","));
              return (
                <fieldset key={field.name} className="flex flex-col gap-2">
                  <legend className="mb-1.5 text-sm font-semibold text-ocean-900">{field.label}</legend>
                  {field.options.map((option) => (
                    <label key={option.value} className="flex min-h-8 cursor-pointer items-center gap-2.5 text-sm text-ocean-950">
                      <input
                        type="checkbox"
                        name={field.name}
                        value={option.value}
                        defaultChecked={checked.has(option.value)}
                        onChange={autoSubmit}
                        className="size-4 accent-ocean-600"
                      />
                      {option.label}
                    </label>
                  ))}
                </fieldset>
              );
            }
          }
        })}
        <div className="flex flex-col gap-2 pt-1">
          <Button type="submit" size="lg" disabled={pending}>
            {labels.apply}
          </Button>
          {active > 0 && (
            <Link href={pageHref(pathname, keep, 1)} scroll={false} className={buttonVariants({ variant: "ghost" })}>
              <XIcon aria-hidden="true" data-icon="inline-start" />
              {labels.reset}
            </Link>
          )}
        </div>
      </form>
    </div>
  );
}
