"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2Icon, LoaderCircleIcon, SendIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";
import { Controller, useForm, useWatch, type Path } from "react-hook-form";
import { z } from "zod";

import { useCaptcha } from "@/components/common/turnstile";
import { selectClass } from "@/components/search/filter-panel";
import { Button, buttonVariants } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Link } from "@/i18n/navigation";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { countryName, RESIDENCE_COUNTRIES } from "@/lib/countries";
import { today } from "@/lib/stay";
import { cn } from "@/lib/utils";
import type { QuoteClient, Schemas } from "@/types";

type Values = Partial<Schemas["QuoteRequestCreateRequest"]>;
type Service = Schemas["RequestedServiceEnum"];

const SERVICES: Service[] = [
  "VOL", "HEBERGEMENT", "CIRCUIT", "VISA", "ASSURANCE", "TRANSPORT", "LOCATION_VEHICULE", "ACTIVITES", "EVENEMENT", "CONSEIL",
];
const TRAVEL_TYPES = ["LOISIRS", "AFFAIRES", "FAMILLE", "LUNE_DE_MIEL", "GROUPE", "PELERINAGE", "ETUDES", "AUTRE"] as const;
const OTHER = "__autre";
const PHONE = /^\+?[0-9 ().-]{6,20}$/;

type QuoteFormProps = {
  destinations: { slug: string; name: string }[];
  /** Valeurs préremplies depuis la fiche d'origine. */
  initial: Values;
};

/**
 * Formulaire de demande de devis (CdC § 18) : projet de voyage puis coordonnées.
 * Envoyé via le relais Next.js ; les erreurs de Django sont affichées sous les
 * champs concernés. Le champ « website » est un piège à robots invisible ; le
 * widget Turnstile fournit le jeton anti-robot.
 */
export function QuoteForm({ destinations, initial }: QuoteFormProps) {
  const t = useTranslations("Quote");
  const locale = useLocale();
  const [sent, setSent] = useState<QuoteClient | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const captcha = useCaptcha("quote");
  const successRef = useRef<HTMLDivElement>(null);
  // Message de succès annoncé et focalisé (le formulaire disparaît).
  useEffect(() => {
    if (sent) successRef.current?.focus();
  }, [sent]);

  const schema = useMemo(
    () =>
      z
        .object({
          destination: z.string(),
          destination_text: z.string().max(200),
          date_departure: z.string(),
          date_return: z.string(),
          // Champs numériques gardés en texte (valeur des inputs), convertis à l'envoi.
          adults: z.string().regex(/^[1-9]\d?$/, t("errors.adults")),
          children: z.string().regex(/^\d{0,2}$/, t("errors.children")),
          travel_type: z.string(),
          budget: z.string().regex(/^\d*$/, t("errors.budget")),
          services_requested: z.array(z.string()),
          accommodation_pref: z.string().max(200),
          transport_pref: z.string().max(200),
          comments: z.string().max(3000),
          first_name: z.string().trim().min(1, t("errors.required")).max(100),
          last_name: z.string().trim().min(1, t("errors.required")).max(100),
          email: z.email(t("errors.email")),
          phone: z.string().trim().regex(PHONE, t("errors.phone")),
          whatsapp: z.string().trim().refine((v) => !v || PHONE.test(v), t("errors.phone")),
          country_code: z.string(),
          consent: z.literal(true, { error: t("errors.consent") }),
          website: z.string(),
        })
        .superRefine((values, ctx) => {
          if ((!values.destination || values.destination === OTHER) && !values.destination_text.trim()) {
            ctx.addIssue({ code: "custom", path: ["destination_text"], message: t("errors.destination") });
          }
          if (values.date_departure && values.date_departure < today()) {
            ctx.addIssue({ code: "custom", path: ["date_departure"], message: t("errors.pastDate") });
          }
          if (values.date_departure && values.date_return && values.date_return < values.date_departure) {
            ctx.addIssue({ code: "custom", path: ["date_return"], message: t("errors.returnBeforeDeparture") });
          }
        }),
    [t],
  );
  type FormValues = z.input<typeof schema>;

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      destination: initial.destination ?? "",
      destination_text: initial.destination_text ?? "",
      date_departure: initial.date_departure ?? "",
      date_return: initial.date_return ?? "",
      adults: String(initial.adults ?? 1),
      children: String(initial.children ?? 0),
      travel_type: "",
      budget: "",
      services_requested: initial.services_requested ?? [],
      accommodation_pref: initial.accommodation_pref ?? "",
      transport_pref: initial.transport_pref ?? "",
      comments: "",
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      whatsapp: "",
      country_code: "CI",
      consent: false as unknown as true,
      website: "",
    },
  });
  const destination = useWatch({ control: form.control, name: "destination" });
  const departure = useWatch({ control: form.control, name: "date_departure" });

  const countries = useMemo(
    () => RESIDENCE_COUNTRIES.map((code) => ({ code, name: countryName(code, locale) })).sort((a, b) => a.name.localeCompare(b.name, locale)),
    [locale],
  );

  async function onSubmit(values: FormValues) {
    setFormError(null);
    if (!captcha.ready) {
      setFormError(t("errors.captcha"));
      return;
    }
    const payload: Values = {
      ...values,
      destination: values.destination && values.destination !== OTHER ? values.destination : null,
      destination_text: values.destination === OTHER || !values.destination ? values.destination_text.trim() : "",
      date_departure: values.date_departure || null,
      date_return: values.date_return || null,
      adults: Number(values.adults),
      children: Number(values.children || 0),
      travel_type: (values.travel_type || "") as Values["travel_type"],
      budget: values.budget || null,
      currency: "XOF",
      services_requested: values.services_requested as Service[],
      source_tour: initial.source_tour ?? null,
      source_offer: initial.source_offer ?? null,
      activities: initial.activities ?? [],
      ...(captcha.token && { captcha_token: captcha.token }),
    };
    try {
      const { data } = await api.post<QuoteClient>("quotes", payload);
      setSent(data);
    } catch (error) {
      captcha.reset(); // un jeton ne sert qu'une fois
      if (error instanceof ApiError && error.code === "validation_error") {
        const fields = error.fieldErrors();
        for (const [name, message] of Object.entries(fields)) {
          if (name in form.getValues()) form.setError(name as Path<FormValues>, { message }, { shouldFocus: true });
        }
        setFormError(fields.non_field_errors ?? t("errors.checkFields"));
      } else if (error instanceof ApiError && error.status === 429) {
        setFormError(t("errors.tooMany"));
      } else {
        setFormError(t("errors.server"));
      }
    }
  }

  if (sent) {
    return (
      <div
        ref={successRef}
        tabIndex={-1}
        role="status"
        className="flex flex-col items-start gap-4 rounded-3xl border border-emerald-200 bg-emerald-50 p-6 outline-none sm:p-8"
      >
        <CheckCircle2Icon aria-hidden="true" className="size-10 text-emerald-700" />
        <h2 className="text-2xl font-bold text-ocean-900">{t("successTitle")}</h2>
        <p className="text-lg text-ocean-950">{t("successText", { reference: sent.reference ?? "" })}</p>
        <p className="text-ocean-950/80">{t("successNext")}</p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link href="/" className={buttonVariants({ variant: "default" })}>
            {t("backHome")}
          </Link>
          <Link href="/destinations" className={buttonVariants({ variant: "outline" })}>
            {t("keepBrowsing")}
          </Link>
        </div>
      </div>
    );
  }

  const text = (name: Path<FormValues>, label: string, props: React.ComponentProps<"input"> = {}, help?: string) => (
    <Controller
      name={name}
      control={form.control}
      render={({ field, fieldState }) => (
        <Field data-invalid={fieldState.invalid}>
          <FieldLabel htmlFor={`quote-${name}`}>{label}</FieldLabel>
          <Input
            {...props}
            id={`quote-${name}`}
            name={field.name}
            value={field.value as string}
            onChange={field.onChange}
            onBlur={field.onBlur}
            ref={field.ref}
            aria-invalid={fieldState.invalid}
            aria-describedby={cn(help && `quote-${name}-help`, fieldState.invalid && `quote-${name}-error`) || undefined}
          />
          {help && <FieldDescription id={`quote-${name}-help`}>{help}</FieldDescription>}
          {fieldState.invalid && <FieldError id={`quote-${name}-error`} errors={[fieldState.error]} />}
        </Field>
      )}
    />
  );

  return (
    <form noValidate onSubmit={form.handleSubmit(onSubmit)} aria-labelledby="quote-form-title" className="flex flex-col gap-8">
      <h2 id="quote-form-title" className="sr-only">
        {t("formTitle")}
      </h2>

      <FieldSet>
        <FieldLegend className="text-xl font-bold text-ocean-900">{t("projectTitle")}</FieldLegend>
        <FieldGroup>
          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              name="destination"
              control={form.control}
              render={({ field }) => (
                <Field>
                  <FieldLabel htmlFor="quote-destination">{t("destination")}</FieldLabel>
                  <select id="quote-destination" {...field} className={selectClass}>
                    <option value="">{t("chooseDestination")}</option>
                    {destinations.map((d) => (
                      <option key={d.slug} value={d.slug}>
                        {d.name}
                      </option>
                    ))}
                    <option value={OTHER}>{t("otherDestination")}</option>
                  </select>
                </Field>
              )}
            />
            {(!destination || destination === OTHER) && text("destination_text", t("destinationText"), { placeholder: t("destinationPlaceholder") })}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {text("date_departure", t("departure"), { type: "date", min: today() })}
            {text("date_return", t("return"), { type: "date", min: departure || today() })}
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {text("adults", t("adults"), { type: "number", min: 1, max: 99, inputMode: "numeric" })}
            {text("children", t("children"), { type: "number", min: 0, max: 99, inputMode: "numeric" })}
            <Controller
              name="travel_type"
              control={form.control}
              render={({ field }) => (
                <Field>
                  <FieldLabel htmlFor="quote-travel_type">{t("travelType")}</FieldLabel>
                  <select id="quote-travel_type" {...field} className={selectClass}>
                    <option value="">{t("chooseTravelType")}</option>
                    {TRAVEL_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {t(`travelTypes.${type}`)}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
            />
          </div>
          <Controller
            name="services_requested"
            control={form.control}
            render={({ field }) => (
              <FieldSet>
                <FieldLegend variant="label">{t("services")}</FieldLegend>
                <div className="grid gap-2 sm:grid-cols-2">
                  {SERVICES.map((service) => {
                    const checked = field.value.includes(service);
                    return (
                      <Field key={service} orientation="horizontal">
                        <Checkbox
                          id={`quote-service-${service}`}
                          checked={checked}
                          onCheckedChange={(on) =>
                            field.onChange(on ? [...field.value, service] : field.value.filter((s) => s !== service))
                          }
                        />
                        <FieldLabel htmlFor={`quote-service-${service}`} className="font-normal">
                          {t(`serviceNames.${service}`)}
                        </FieldLabel>
                      </Field>
                    );
                  })}
                </div>
              </FieldSet>
            )}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            {text("accommodation_pref", t("accommodation"), { placeholder: t("accommodationPlaceholder") })}
            {text("transport_pref", t("transport"), { placeholder: t("transportPlaceholder") })}
          </div>
          {text("budget", t("budget"), { inputMode: "numeric", placeholder: "1 500 000" }, t("budgetHelp"))}
          <Controller
            name="comments"
            control={form.control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="quote-comments">{t("comments")}</FieldLabel>
                <Textarea {...field} id="quote-comments" rows={4} placeholder={t("commentsPlaceholder")} aria-invalid={fieldState.invalid} />
                {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
              </Field>
            )}
          />
        </FieldGroup>
      </FieldSet>

      <FieldSet>
        <FieldLegend className="text-xl font-bold text-ocean-900">{t("contactTitle")}</FieldLegend>
        <FieldGroup>
          <div className="grid gap-4 sm:grid-cols-2">
            {text("first_name", t("firstName"), { autoComplete: "given-name" })}
            {text("last_name", t("lastName"), { autoComplete: "family-name" })}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {text("email", t("email"), { type: "email", autoComplete: "email" })}
            {text("phone", t("phone"), { type: "tel", autoComplete: "tel", placeholder: "+225 07 00 00 00 00" })}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {text("whatsapp", t("whatsapp"), { type: "tel", placeholder: "+225 07 00 00 00 00" }, t("whatsappHelp"))}
            <Controller
              name="country_code"
              control={form.control}
              render={({ field }) => (
                <Field>
                  <FieldLabel htmlFor="quote-country">{t("country")}</FieldLabel>
                  <select id="quote-country" {...field} autoComplete="country" className={selectClass}>
                    {countries.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
            />
          </div>
          {/* Piège à robots : invisible et ignoré par les lecteurs d'écran. */}
          <div aria-hidden="true" className="absolute -start-[9999px] size-px overflow-hidden">
            <label htmlFor="quote-website">Website</label>
            <input id="quote-website" tabIndex={-1} autoComplete="off" {...form.register("website")} />
          </div>
          <Controller
            name="consent"
            control={form.control}
            render={({ field, fieldState }) => (
              <Field orientation="horizontal" data-invalid={fieldState.invalid}>
                <Checkbox id="quote-consent" checked={field.value} onCheckedChange={field.onChange} aria-invalid={fieldState.invalid} />
                <div className="flex flex-col gap-1">
                  <FieldLabel htmlFor="quote-consent" className="font-normal">
                    {t("consent")}
                  </FieldLabel>
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </div>
              </Field>
            )}
          />
        </FieldGroup>
      </FieldSet>

      {captcha.widget}
      {formError && (
        <p role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800">
          {formError}
        </p>
      )}
      <Button type="submit" variant="cta" size="lg" className="w-full sm:w-fit" disabled={form.formState.isSubmitting}>
        {form.formState.isSubmitting ? (
          <LoaderCircleIcon aria-hidden="true" data-icon="inline-start" className="animate-spin" />
        ) : (
          <SendIcon aria-hidden="true" data-icon="inline-start" />
        )}
        {t("submit")}
      </Button>
    </form>
  );
}
