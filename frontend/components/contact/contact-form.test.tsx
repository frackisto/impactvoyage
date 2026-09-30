import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import messages from "@/messages/fr.json";

import { ContactForm } from "./contact-form";

/**
 * Réponse simulée de l'API. Une fonction ordinaire plutôt qu'un vi.fn() : Vitest
 * signale comme erreur la promesse rejetée d'un espion, même attrapée par le composant.
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
  Link: ({ children, href, ...props }: Record<string, unknown> & { children: React.ReactNode }) => (
    <a href={String(href)} {...props}>
      {children}
    </a>
  ),
}));

function renderForm() {
  render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      <ContactForm />
    </NextIntlClientProvider>,
  );
}

async function fillValid() {
  await userEvent.type(screen.getByLabelText("Nom complet"), "Awa Koné");
  await userEvent.type(screen.getByLabelText("Adresse email"), "awa@example.com");
  await userEvent.selectOptions(screen.getByLabelText("Objet"), "visa");
  await userEvent.type(screen.getByLabelText("Message"), "Quels documents pour un visa Schengen ?");
}

const submit = () => userEvent.click(screen.getByRole("button", { name: "Envoyer le message" }));

describe("ContactForm", () => {
  beforeEach(() => {
    sent.length = 0;
    respond = async () => ({ data: { message: "ok" } });
  });

  it("contrôles dans le navigateur avant tout envoi", async () => {
    renderForm();
    await userEvent.type(screen.getByLabelText("Téléphone"), "abc");
    await submit();
    expect(await screen.findByText("Choisissez l'objet de votre message.")).toBeInTheDocument();
    expect(screen.getByText("Numéro de téléphone invalide.")).toBeInTheDocument();
    expect(screen.getByLabelText("Nom complet")).toHaveAttribute("aria-invalid", "true");
    expect(sent).toHaveLength(0);
  });

  it("envoie l'objet dans la langue du visiteur puis confirme l'envoi", async () => {
    renderForm();
    await fillValid();
    await submit();
    expect(await screen.findByRole("status")).toHaveTextContent("Message envoyé !");
    expect(sent).toEqual([["contact", expect.objectContaining({
      name: "Awa Koné", email: "awa@example.com", subject: "Visa et formalités", website: "",
    })]]);
  });

  it("erreurs de Django affichées sous les champs", async () => {
    respond = async () => {
      throw new ApiError(400, "validation_error", "Données invalides.", {
        email: ["Adresse refusée par le serveur."],
      });
    };
    renderForm();
    await fillValid();
    await submit();
    expect(await screen.findByText("Adresse refusée par le serveur.")).toBeInTheDocument();
    expect(screen.getByText("Certains champs sont à corriger.")).toBeInTheDocument();
  });

  it("limite d'envoi : message clair", async () => {
    respond = async () => {
      throw new ApiError(429, "throttled", "Trop de requêtes.");
    };
    renderForm();
    await fillValid();
    await submit();
    expect(await screen.findByText(/Trop de messages envoyés/)).toBeInTheDocument();
  });
});
