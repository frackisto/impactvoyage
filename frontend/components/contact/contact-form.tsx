"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2Icon, LoaderCircleIcon, SendIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";
import { Controller, useForm, type Path } from "react-hook-form";
import { z } from "zod";

import { selectClass } from "@/components/search/filter-panel";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Link } from "@/i18n/navigation";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/utils";

const PHONE = /^\+?[0-9 ().-]{6,20}$/;
export const CONTACT_SUBJECTS = ["info", "booking", "visa", "complaint", "partnership", "other"] as const;

/**
 * Formulaire de contact (CdC § 19), envoyé via le relais Next.js. L'objet
 * choisi est transmis dans la langue du visiteur. Le champ « website » est un
 * piège à robots invisible.
 */
export function ContactForm() {
  const t = useTranslations("Contact");
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const successRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (sent) successRef.current?.focus();
  }, [sent]);

  const schema = useMemo(
    () =>
      z.object({
        name: z.string().trim().min(1, t("errors.required")).max(150),
        email: z.email(t("errors.email")),
        phone: z.string().trim().refine((v) => !v || PHONE.test(v), t("errors.phone")),
        subject: z.string().min(1, t("errors.subject")),
        message: z.string().trim().min(10, t("errors.messageShort")).max(5000, t("errors.messageLong")),
        website: z.string(),
      }),
    [t],
  );
  type FormValues = z.input<typeof schema>;

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", phone: "", subject: "", message: "", website: "" },
  });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await api.post("contact", { ...values, subject: t(`subjects.${values.subject as (typeof CONTACT_SUBJECTS)[number]}`) });
      setSent(true);
    } catch (error) {
      if (error instanceof ApiError && error.code === "validation_error") {
        const fields = error.fieldErrors();
        for (const [name, message] of Object.entries(fields)) {
          if (name in form.getValues() && name !== "subject") form.setError(name as Path<FormValues>, { message }, { shouldFocus: true });
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
        <p className="text-lg text-ocean-950">{t("successText")}</p>
      </div>
    );
  }

  const text = (name: Path<FormValues>, label: string, props: React.ComponentProps<"input"> = {}) => (
    <Controller
      name={name}
      control={form.control}
      render={({ field, fieldState }) => (
        <Field data-invalid={fieldState.invalid}>
          <FieldLabel htmlFor={`contact-${name}`}>{label}</FieldLabel>
          <Input
            {...props}
            id={`contact-${name}`}
            name={field.name}
            value={field.value}
            onChange={field.onChange}
            onBlur={field.onBlur}
            ref={field.ref}
            aria-invalid={fieldState.invalid}
            aria-describedby={fieldState.invalid ? `contact-${name}-error` : undefined}
          />
          {fieldState.invalid && <FieldError id={`contact-${name}-error`} errors={[fieldState.error]} />}
        </Field>
      )}
    />
  );

  return (
    <form noValidate onSubmit={form.handleSubmit(onSubmit)} aria-labelledby="contact-form-title" className="flex flex-col gap-5">
      <h2 id="contact-form-title" className="text-2xl font-bold text-ocean-900">
        {t("formTitle")}
      </h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {text("name", t("name"), { autoComplete: "name" })}
        {text("email", t("email"), { type: "email", autoComplete: "email" })}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {text("phone", t("phone"), { type: "tel", autoComplete: "tel", placeholder: "+225 07 00 00 00 00" })}
        <Controller
          name="subject"
          control={form.control}
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor="contact-subject">{t("subject")}</FieldLabel>
              <select
                id="contact-subject"
                {...field}
                aria-invalid={fieldState.invalid}
                aria-describedby={fieldState.invalid ? "contact-subject-error" : undefined}
                className={cn(selectClass, fieldState.invalid && "border-destructive")}
              >
                <option value="">{t("chooseSubject")}</option>
                {CONTACT_SUBJECTS.map((subject) => (
                  <option key={subject} value={subject}>
                    {t(`subjects.${subject}`)}
                  </option>
                ))}
              </select>
              {fieldState.invalid && <FieldError id="contact-subject-error" errors={[fieldState.error]} />}
            </Field>
          )}
        />
      </div>
      <Controller
        name="message"
        control={form.control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="contact-message">{t("message")}</FieldLabel>
            <Textarea
              {...field}
              id="contact-message"
              rows={6}
              aria-invalid={fieldState.invalid}
              aria-describedby={fieldState.invalid ? "contact-message-error" : undefined}
            />
            {fieldState.invalid && <FieldError id="contact-message-error" errors={[fieldState.error]} />}
          </Field>
        )}
      />
      {/* Piège à robots : invisible et ignoré par les lecteurs d'écran. */}
      <div aria-hidden="true" className="absolute -start-[9999px] size-px overflow-hidden">
        <label htmlFor="contact-website">Website</label>
        <input id="contact-website" tabIndex={-1} autoComplete="off" {...form.register("website")} />
      </div>
      <p className="text-sm text-muted-foreground">
        {t("privacyNote")}{" "}
        <Link href="/confidentialite" className="font-semibold text-ocean-700 underline underline-offset-4">
          {t("privacyLink")}
        </Link>
      </p>
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
