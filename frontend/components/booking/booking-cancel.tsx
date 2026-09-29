"use client";

import { LoaderCircleIcon, XIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

/**
 * Annulation par le client, avec le jeton de son lien de suivi, tant que
 * l'agence n'a pas confirmé. Demande une confirmation et un motif facultatif.
 */
export function BookingCancel({ reference, token }: { reference: string; token: string }) {
  const t = useTranslations("BookingTracking");
  const router = useRouter();
  const [step, setStep] = useState<"idle" | "confirm" | "busy">("idle");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const reasonId = useId();

  async function cancel() {
    setStep("busy");
    setError(null);
    try {
      await api.post(`bookings/${encodeURIComponent(reference)}/cancel`, { token, reason: reason.trim() });
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ApiError && err.code === "contact_agency"
          ? t("cancelTooLate")
          : err instanceof ApiError && err.status === 429
            ? t("tooMany")
            : t("cancelError"),
      );
      setStep("idle");
    }
  }

  return (
    <div className="flex flex-col gap-4" aria-busy={step === "busy"}>
      {error && (
        <p role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800">
          {error}
        </p>
      )}
      {step === "idle" ? (
        <Button variant="outline" className="w-full sm:w-fit" onClick={() => setStep("confirm")}>
          <XIcon aria-hidden="true" data-icon="inline-start" />
          {t("cancel")}
        </Button>
      ) : (
        <div className="flex flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50/60 p-5">
          <p className="font-semibold text-ocean-900">{t("confirmCancel")}</p>
          <label htmlFor={reasonId} className="text-sm font-semibold text-ocean-900">
            {t("cancelReason")}
          </label>
          <Textarea id={reasonId} rows={3} maxLength={2000} value={reason} onChange={(e) => setReason(e.currentTarget.value)} />
          <div className="flex flex-wrap gap-2">
            <Button variant="destructive" disabled={step === "busy"} onClick={cancel}>
              {step === "busy" ? (
                <LoaderCircleIcon aria-hidden="true" data-icon="inline-start" className="animate-spin" />
              ) : (
                <XIcon aria-hidden="true" data-icon="inline-start" />
              )}
              {t("confirmCancelButton")}
            </Button>
            <Button variant="ghost" disabled={step === "busy"} onClick={() => setStep("idle")}>
              {t("keep")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
