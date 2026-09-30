import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import messages from "@/messages/fr.json";

/**
 * Widget Turnstile dans un formulaire (formulaire de contact). La clé du site est lue
 * au chargement du module : elle est définie avant d'importer le formulaire.
 */
let respond: () => Promise<unknown> = async () => ({ data: {} });
const sent: unknown[][] = [];

vi.mock("@/lib/api/client", () => ({
  api: {
    post: (...args: unknown[]) => {
      sent.push(args);
      return respond();
    },
  },
}));
vi.mock("@/i18n/navigation", () => ({
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

type Options = { sitekey: string; action: string; language: string; callback: (token: string) => void };
const widgets: Options[] = [];
const removed: string[] = [];
let solve = true;

async function renderContactForm() {
  vi.resetModules();
  vi.stubEnv("NEXT_PUBLIC_TURNSTILE_SITE_KEY", "cle-du-site");
  const { ContactForm } = await import("@/components/contact/contact-form");
  render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      <ContactForm />
    </NextIntlClientProvider>,
  );
}

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText("Nom complet"), "Awa Koné");
  await userEvent.type(screen.getByLabelText("Adresse email"), "awa@example.com");
  await userEvent.selectOptions(screen.getByLabelText("Objet"), "visa");
  await userEvent.type(screen.getByLabelText("Message"), "Quels documents pour un visa Schengen ?");
  await userEvent.click(screen.getByRole("button", { name: "Envoyer le message" }));
}

describe("Turnstile", () => {
  beforeEach(() => {
    sent.length = 0;
    widgets.length = 0;
    removed.length = 0;
    solve = true;
    respond = async () => ({ data: {} });
    window.turnstile = {
      render: (_element, options) => {
        const typed = options as Options;
        widgets.push(typed);
        if (solve) typed.callback(`jeton-${widgets.length}`);
        return `widget-${widgets.length}`;
      },
      remove: (id) => {
        removed.push(id);
      },
    };
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    delete window.turnstile;
  });

  it("affiche le widget dans la langue de la page et envoie son jeton", async () => {
    await renderContactForm();
    expect(await screen.findByTestId("turnstile")).toBeInTheDocument();
    expect(widgets[0]).toMatchObject({ sitekey: "cle-du-site", action: "contact", language: "fr" });

    await fillAndSubmit();
    expect(sent[0][1]).toMatchObject({ captcha_token: "jeton-1" });
  });

  it("n'envoie rien tant que la vérification n'a pas abouti", async () => {
    solve = false;
    await renderContactForm();
    await fillAndSubmit();
    expect(sent).toHaveLength(0);
    expect(await screen.findByRole("alert")).toHaveTextContent("Vérification anti-robot en cours");
  });

  it("demande un nouveau jeton après une erreur (un jeton ne sert qu'une fois)", async () => {
    await renderContactForm();
    // Même instance du module que le formulaire (modules rechargés par renderContactForm).
    const { ApiError } = await import("@/lib/api/errors");
    respond = async () => {
      throw new ApiError(400, "validation_error", "Données invalides.", {
        non_field_errors: ["La vérification anti-robot a échoué ou a expiré. Réessayez."],
      });
    };
    await fillAndSubmit();
    expect(await screen.findByRole("alert")).toHaveTextContent("anti-robot a échoué");
    expect(removed).toContain("widget-1");
    expect(widgets).toHaveLength(2);

    respond = async () => ({ data: {} });
    await userEvent.click(screen.getByRole("button", { name: "Envoyer le message" }));
    expect(sent[1][1]).toMatchObject({ captcha_token: "jeton-2" });
  });
});
