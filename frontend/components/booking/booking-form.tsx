"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { LoaderCircleIcon, SendIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { Controller, useForm, useWatch, type Path } from "react-hook-form";
import { z } from "zod";

import { Price } from "@/components/common/price";
import { useCaptcha } from "@/components/common/turnstile";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Link, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { multiplyMoney } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Money, Schemas } from "@/types";

type Payload = Schemas["BookingRequestRequest"];
type Created = Schemas["BookingCreated"];

const PHONE = /^\+?[0-9 ().-]{6,20}$/;

/** Ce que le formulaire doit savoir de la prestation (voir BookingDraft, côté serveur). */
export type BookingFormItem = {
  kind: Schemas["BookingKindEnum"];
  objectId: number;
  start?: string;
  end?: string;
  quantityKind: "travelers" | "rooms" | "participants" | null;
  quantity: number;
  maxQuantity: number;
  unitPrice: Money | null;
  periods: number;
  withLocations: boolean;
  href: string;
};

/**
 * Demande de réservation (CdC § 12, § 13) : quantité, coordonnées et
 * consentement. Aucun prix n'est envoyé : le total affiché est indicatif et
 * Django le recalcule. Après l'envoi, le client arrive sur sa page de suivi.
 * Le champ « website » est un piège à robots invisible ; le widget Turnstile
 * fournit le jeton anti-robot.
 */
export function BookingForm({ item }: { item: BookingFormItem }) {
  const t = useTranslations("Booking");
  const router = useRouter();
  const [formError, setFormError] = useState<{ message: string; backToOffer?: boolean } | null>(null);
  const captcha = useCaptcha("booking");

  const schema = useMemo(
    () =>
      z.object({
        // Gardée en texte (valeur de l'input), convertie à l'envoi.
        quantity: z
          .string()
          .regex(/^\d{1,2}$/, t("errors.quantity", { max: item.maxQuantity }))
          .refine((v) => Number(v) >= 1 && Number(v) <= item.maxQuantity, t("errors.quantity", { max: item.maxQuantity })),
        pickup_location: z.string().max(200),
        dropoff_location: z.string().max(200),
        contact_name: z.string().trim().min(2, t("errors.required")).max(200),
        contact_email: z.email(t("errors.email")),
        contact_phone: z.string().trim().regex(PHONE, t("errors.phone")),
        customer_comments: z.string().max(2000),
        consent: z.literal(true, { error: t("errors.consent") }),
        website: z.string(),
      }),
    [t, item.maxQuantity],
  );
  type FormValues = z.input<typeof schema>;

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      quantity: String(item.quantity),
      pickup_location: "",
      dropoff_location: "",
      contact_name: "",
      contact_email: "",
      contact_phone: "",
      customer_comments: "",
      consent: false as unknown as true,
      website: "",
    },
  });
  const quantity = Number(useWatch({ control: form.control, name: "quantity" })) || 0;
  const total =
    item.unitPrice && quantity >= 1 && quantity <= item.maxQuantity ? multiplyMoney(item.unitPrice, item.periods * quantity) : null;

  async function onSubmit(values: FormValues) {
    setFormError(null);
    if (!captcha.ready) {
      setFormError({ message: t("errors.captcha") });
      return;
    }
    const payload: Payload = {
      contact_name: values.contact_name.trim(),
      contact_email: values.contact_email,
      contact_phone: values.contact_phone.trim(),
      customer_comments: values.customer_comments.trim(),
      consent: values.consent,
      website: values.website,
      ...(captcha.token && { captcha_token: captcha.token }),
      items: [
        {
          kind: item.kind,
          object_id: item.objectId,
          start_date: item.start ?? null,
          end_date: item.end ?? null,
          quantity: Number(values.quantity),
          pickup_location: values.pickup_location.trim(),
          dropoff_location: values.dropoff_location.trim(),
        },
      ],
    };
    try {
      const { data } = await api.post<Created>("bookings", payload);
      const query = new URLSearchParams({ token: data.access_token, sent: "1" });
      router.push(`/reservation/${encodeURIComponent(data.reference ?? "")}?${query}`);
    } catch (error) {
      captcha.reset(); // un jeton ne sert qu'une fois
      if (error instanceof ApiError && error.code === "validation_error") {
        const fields = error.fieldErrors();
        for (const [name, message] of Object.entries(fields)) {
          if (name in form.getValues()) form.setError(name as Path<FormValues>, { message }, { shouldFocus: true });
        }
        setFormError({ message: fields.non_field_errors ?? t("errors.checkFields") });
      } else if (error instanceof ApiError && error.code === "not_available") {
        setFormError({ message: t("errors.notAvailable"), backToOffer: true });
      } else if (error instanceof ApiError && ["date_in_past", "offer_not_found", "invalid_period"].includes(error.code)) {
        setFormError({ message: t("errors.offerChanged"), backToOffer: true });
      } else if (error instanceof ApiError && error.status === 429) {
        setFormError({ message: t("errors.tooMany") });
      } else {
        setFormError({ message: t("errors.server") });
      }
    }
  }

  const text = (name: Path<FormValues>, label: string, props: React.ComponentProps<"input"> = {}, help?: string) => (
    <Controller
      name={name}
      control={form.control}
      render={({ field, fieldState }) => (
        <Field data-invalid={fieldState.invalid}>
          <FieldLabel htmlFor={`booking-${name}`}>{label}</FieldLabel>
          <Input
            {...props}
            id={`booking-${name}`}
            name={field.name}
            value={field.value as string}
            onChange={field.onChange}
            onBlur={field.onBlur}
            ref={field.ref}
            aria-invalid={fieldState.invalid}
            aria-describedby={cn(help && `booking-${name}-help`, fieldState.invalid && `booking-${name}-error`) || undefined}
          />
          {help && <FieldDescription id={`booking-${name}-help`}>{help}</FieldDescription>}
          {fieldState.invalid && <FieldError id={`booking-${name}-error`} errors={[fieldState.error]} />}
        </Field>
      )}
    />
  );

  return (
    <form noValidate onSubmit={form.handleSubmit(onSubmit)} aria-labelledby="booking-form-title" className="flex flex-col gap-8">
      <h2 id="booking-form-title" className="sr-only">
        {t("formTitle")}
      </h2>

      {(item.quantityKind || item.withLocations) && (
        <FieldSet>
          <FieldLegend className="text-xl font-bold text-ocean-900">{t("detailsTitle")}</FieldLegend>
          <FieldGroup>
            {item.quantityKind &&
              text(
                "quantity",
                t(`quantity.${item.quantityKind}`),
                { type: "number", min: 1, max: item.maxQuantity, inputMode: "numeric", className: "sm:max-w-40" },
                item.maxQuantity > 1 ? t("quantityHelp", { max: item.maxQuantity }) : undefined,
              )}
            {item.withLocations && (
              <div className="grid gap-4 sm:grid-cols-2">
                {text("pickup_location", t("pickup"), { placeholder: t("locationPlaceholder") })}
                {text("dropoff_location", t("dropoff"), { placeholder: t("locationPlaceholder") })}
              </div>
            )}
          </FieldGroup>
        </FieldSet>
      )}

      <FieldSet>
        <FieldLegend className="text-xl font-bold text-ocean-900">{t("contactTitle")}</FieldLegend>
        <FieldGroup>
          {text("contact_name", t("name"), { autoComplete: "name" })}
          <div className="grid gap-4 sm:grid-cols-2">
            {text("contact_email", t("email"), { type: "email", autoComplete: "email" }, t("emailHelp"))}
            {text("contact_phone", t("phone"), { type: "tel", autoComplete: "tel", placeholder: "+225 07 00 00 00 00" })}
          </div>
          <Controller
            name="customer_comments"
            control={form.control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="booking-comments">{t("comments")}</FieldLabel>
                <Textarea {...field} id="booking-comments" rows={4} placeholder={t("commentsPlaceholder")} aria-invalid={fieldState.invalid} />
                {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
              </Field>
            )}
          />
          {/* Piège à robots : invisible et ignoré par les lecteurs d'écran. */}
          <div aria-hidden="true" className="absolute -start-[9999px] size-px overflow-hidden">
            <label htmlFor="booking-website">Website</label>
            <input id="booking-website" tabIndex={-1} autoComplete="off" {...form.register("website")} />
          </div>
          <Controller
            name="consent"
            control={form.control}
            render={({ field, fieldState }) => (
              <Field orientation="horizontal" data-invalid={fieldState.invalid}>
                <Checkbox id="booking-consent" checked={field.value} onCheckedChange={field.onChange} aria-invalid={fieldState.invalid} />
                <div className="flex flex-col gap-1">
                  <FieldLabel htmlFor="booking-consent" className="font-normal">
                    {t("consent")}
                  </FieldLabel>
                  <FieldDescription>
                    {t.rich("consentLinks", {
                      terms: (chunks) => (
                        <Link href="/conditions-generales" className="underline">
                          {chunks}
                        </Link>
                      ),
                      privacy: (chunks) => (
                        <Link href="/confidentialite" className="underline">
                          {chunks}
                        </Link>
                      ),
                    })}
                  </FieldDescription>
                  {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                </div>
              </Field>
            )}
          />
        </FieldGroup>
      </FieldSet>

      {captcha.widget}
      {formError && (
        <div role="alert" className="flex flex-col items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800">
          <p>{formError.message}</p>
          {formError.backToOffer && (
            <Link href={item.href} className="font-semibold underline">
              {t("backToOffer")}
            </Link>
          )}
        </div>
      )}

      <div className="flex flex-col gap-4 rounded-3xl bg-ocean-50/70 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-ocean-900">{t("estimatedTotal")}</span>
          {total ? <Price value={total} /> : <span className="text-ocean-950">{t("priceOnRequest")}</span>}
          <span className="text-xs text-muted-foreground">{t("totalNote")}</span>
        </div>
        <Button type="submit" variant="cta" size="lg" className="w-full sm:w-fit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? (
            <LoaderCircleIcon aria-hidden="true" data-icon="inline-start" className="animate-spin" />
          ) : (
            <SendIcon aria-hidden="true" data-icon="inline-start" />
          )}
          {t("submit")}
        </Button>
      </div>
    </form>
  );
}
