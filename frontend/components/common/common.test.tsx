import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import messages from "@/messages/fr.json";

import { OfferBadge } from "./offer-badge";
import { Price } from "./price";
import { Rating } from "./rating";

function renderFr(ui: React.ReactNode) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("Price", () => {
  it("affiche le prix d'origine, l'unité et « À partir de »", () => {
    renderFr(<Price value={{ amount: "450000.00", currency: "XOF" }} from unit="person" />);
    expect(screen.getByText(/450\s000\sF\sCFA/)).toBeInTheDocument();
    expect(screen.getByText("À partir de")).toBeInTheDocument();
    expect(screen.getByText(/\/ pers\./)).toBeInTheDocument();
  });

  it("signale une conversion comme indicative", () => {
    renderFr(
      <Price value={{ amount: "450000.00", currency: "XOF", display: { amount: "686.02", currency: "EUR" } }} />,
    );
    expect(screen.getByText(/686,02\s€/)).toBeInTheDocument();
    expect(screen.getByText(/prix indicatif/)).toBeInTheDocument();
  });

  it("n'affiche rien sans prix", () => {
    const { container } = renderFr(<Price value={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Rating", () => {
  it("donne une note lisible par les lecteurs d'écran", () => {
    renderFr(<Rating value={4.6} count={12} />);
    expect(screen.getByText("Note : 4,6 sur 5")).toBeInTheDocument();
    expect(screen.getByText("(12 avis)")).toBeInTheDocument();
  });
});

describe("OfferBadge", () => {
  it("traduit le code du badge", () => {
    renderFr(<OfferBadge code="DERNIERES_PLACES" />);
    expect(screen.getByText("Dernières places")).toBeInTheDocument();
  });
});
