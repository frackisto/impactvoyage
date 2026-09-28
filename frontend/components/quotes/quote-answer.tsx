"use client";

import { CheckIcon, LoaderCircleIcon, XIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { Booking } from "@/types";

type Step = "idle" | "confirm-accept" | "confirm-decline" | "busy";

/**
 * Réponse du client à la proposition (lien secret reçu par email) : accepter
 * crée la réservation, décliner peut s'accompagner d'un motif. Chaque choix
 * demande une confirmation.
 */
export function QuoteAnswer({ reference, token }: { reference: string; token: string }) {
  const t = useTranslations("QuoteTracking");
  const router = useRouter();
  const [step, setStep] = useState<Step>("idle");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<Booking | null>(null);
  const reasonId = useId();

  async function send(action: "accept" | "decline") {
    setStep("busy");
    setError(null);
    try {
      const path = `quotes/${encodeURIComponent(reference)}/${action}`;
      if (action === "accept") {
        const { data } = await api.post<Booking>(path, { token });
        setBooking(data);
      } else {
        await api.post(path, { token, reason: reason.trim() });
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError && err.message ? err.message : t("errorAnswer"));
      setStep("idle");
    }
  }

  if (booking) {
    return (
      <p role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900">
        {t("acceptedText", { reference: booking.reference ?? "" })}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4" aria-busy={step === "busy"}>
      {error && (
        <p role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800">
          {error}
        </p>
      )}

      {step === "confirm-accept" ? (
        <div className="flex flex-col gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
          <p className="font-semibold text-ocean-900">{t("confirmAccept")}</p>
          <div className="flex flex-wrap gap-2">
            <Button variant="cta" onClick={() => send("accept")}>
              <CheckIcon aria-hidden="true" data-icon="inline-start" />
              {t("confirmAcceptButton")}
            </Button>
            <Button variant="ghost" onClick={() => setStep("idle")}>
              {t("cancel")}
            </Button>
          </div>
        </div>
      ) : step === "confirm-decline" ? (
        <div className="flex flex-col gap-3 rounded-2xl border p-5">
          <label htmlFor={reasonId} className="font-semibold text-ocean-900">
            {t("declineReason")}
          </label>
          <Textarea id={reasonId} rows={3} maxLength={1000} value={reason} onChange={(e) => setReason(e.currentTarget.value)} />
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => send("decline")}>
              <XIcon aria-hidden="true" data-icon="inline-start" />
              {t("confirmDeclineButton")}
            </Button>
            <Button variant="ghost" onClick={() => setStep("idle")}>
              {t("cancel")}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3">
          <Button variant="cta" size="lg" disabled={step === "busy"} onClick={() => setStep("confirm-accept")}>
            {step === "busy" ? (
              <LoaderCircleIcon aria-hidden="true" data-icon="inline-start" className="animate-spin" />
            ) : (
              <CheckIcon aria-hidden="true" data-icon="inline-start" />
            )}
            {t("accept")}
          </Button>
          <Button variant="outline" size="lg" disabled={step === "busy"} onClick={() => setStep("confirm-decline")}>
            {t("decline")}
          </Button>
        </div>
      )}
    </div>
  );
}
