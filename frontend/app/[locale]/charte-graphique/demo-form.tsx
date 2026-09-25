"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({
  name: z.string().min(2, "Indiquez votre nom (2 caractères minimum)."),
  email: z.email("Adresse email invalide."),
  message: z.string().min(10, "Votre message doit faire au moins 10 caractères."),
  consent: z.literal(true, { error: "Votre accord est nécessaire pour envoyer le formulaire." }),
});

type Values = z.infer<typeof schema>;

/**
 * Modèle de formulaire du site : React Hook Form + Zod, erreurs reliées aux
 * champs (aria-invalid, aria-describedby), notification de succès.
 */
export function DemoForm() {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", message: "", consent: false as unknown as true },
  });

  return (
    <form
      noValidate
      onSubmit={form.handleSubmit(() => {
        toast.success("Message envoyé", { description: "Nous vous répondons rapidement." });
        form.reset();
      })}
      className="max-w-xl"
    >
      <FieldGroup>
        {(["name", "email"] as const).map((name) => (
          <Controller
            key={name}
            name={name}
            control={form.control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor={`demo-${name}`}>{name === "name" ? "Nom" : "Email"}</FieldLabel>
                <Input
                  {...field}
                  id={`demo-${name}`}
                  type={name === "email" ? "email" : "text"}
                  autoComplete={name}
                  aria-invalid={fieldState.invalid}
                  aria-describedby={fieldState.invalid ? `demo-${name}-error` : undefined}
                />
                {fieldState.invalid && <FieldError id={`demo-${name}-error`} errors={[fieldState.error]} />}
              </Field>
            )}
          />
        ))}
        <Controller
          name="message"
          control={form.control}
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor="demo-message">Message</FieldLabel>
              <Textarea
                {...field}
                id="demo-message"
                rows={4}
                aria-invalid={fieldState.invalid}
                aria-describedby="demo-message-help"
              />
              <FieldDescription id="demo-message-help">Précisez vos dates et votre budget.</FieldDescription>
              {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
            </Field>
          )}
        />
        <Controller
          name="consent"
          control={form.control}
          render={({ field, fieldState }) => (
            <Field orientation="horizontal" data-invalid={fieldState.invalid}>
              <Checkbox
                id="demo-consent"
                checked={field.value}
                onCheckedChange={field.onChange}
                aria-invalid={fieldState.invalid}
              />
              <FieldLabel htmlFor="demo-consent" className="font-normal">
                J&apos;accepte que mes données soient utilisées pour traiter ma demande.
              </FieldLabel>
              {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
            </Field>
          )}
        />
        <Button type="submit" size="lg" className="w-fit">
          Envoyer
        </Button>
      </FieldGroup>
    </form>
  );
}
