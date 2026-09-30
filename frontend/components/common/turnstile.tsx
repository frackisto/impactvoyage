"use client";

import { useLocale } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { TURNSTILE_ORIGIN } from "@/lib/security";

/**
 * Anti-robot des formulaires publics (CdC § 29, Phase 23) : widget Cloudflare
 * Turnstile. Le jeton obtenu est envoyé avec le formulaire (`captcha_token`) et
 * vérifié par Django (backend/apps/core/captcha.py). Sans clé de site
 * (NEXT_PUBLIC_TURNSTILE_SITE_KEY vide : développement, tests), rien n'est affiché.
 */
export const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "";

type TurnstileApi = {
  render: (element: HTMLElement, options: Record<string, unknown>) => string;
  remove: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

let loading: Promise<TurnstileApi> | null = null;

/** Charge le script de Turnstile une seule fois (autorisé par la CSP : « strict-dynamic »). */
export function loadTurnstile(): Promise<TurnstileApi> {
  if (window.turnstile) return Promise.resolve(window.turnstile);
  loading ??= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `${TURNSTILE_ORIGIN}/turnstile/v0/api.js?render=explicit`;
    script.async = true;
    script.onload = () => (window.turnstile ? resolve(window.turnstile) : reject(new Error("turnstile")));
    script.onerror = () => {
      loading = null;
      reject(new Error("turnstile"));
    };
    document.head.appendChild(script);
  });
  return loading;
}

type TurnstileProps = {
  /** Jeton valide, ou chaîne vide quand il expire ou que la vérification échoue. */
  onToken: (token: string) => void;
  /** Nom de l'action (statistiques Cloudflare), ex. « contact ». */
  action: string;
};

export function Turnstile({ onToken, action }: TurnstileProps) {
  const container = useRef<HTMLDivElement>(null);
  const locale = useLocale();
  const callback = useRef(onToken);
  useEffect(() => {
    callback.current = onToken;
  }, [onToken]);

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY) return;
    let widgetId: string | undefined;
    let cancelled = false;
    loadTurnstile()
      .then((turnstile) => {
        if (cancelled || !container.current) return;
        widgetId = turnstile.render(container.current, {
          sitekey: TURNSTILE_SITE_KEY,
          action,
          language: locale,
          size: "flexible",
          "refresh-expired": "auto",
          callback: (token: string) => callback.current(token),
          "expired-callback": () => callback.current(""),
          "error-callback": () => callback.current(""),
        });
      })
      .catch(() => callback.current(""));
    return () => {
      cancelled = true;
      if (widgetId) window.turnstile?.remove(widgetId);
    };
  }, [action, locale]);

  if (!TURNSTILE_SITE_KEY) return null;
  return <div ref={container} data-testid="turnstile" className="min-h-[65px]" />;
}

/**
 * État anti-robot d'un formulaire : `token` à envoyer, `ready` (jeton obtenu ou
 * vérification désactivée), `reset()` après une réponse d'erreur (un jeton ne sert
 * qu'une fois) et `widget` à placer avant le bouton d'envoi.
 */
export function useCaptcha(action: string) {
  const [token, setToken] = useState("");
  const [generation, setGeneration] = useState(0);
  const reset = useCallback(() => {
    setToken("");
    setGeneration((value) => value + 1);
  }, []);
  return {
    token,
    ready: !TURNSTILE_SITE_KEY || Boolean(token),
    reset,
    widget: <Turnstile key={generation} action={action} onToken={setToken} />,
  };
}
