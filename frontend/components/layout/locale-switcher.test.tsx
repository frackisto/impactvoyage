import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import messages from "@/messages/fr.json";

import { LocaleSwitcher } from "./locale-switcher";

vi.mock("@/i18n/navigation", () => ({
  usePathname: () => "/destinations",
  Link: ({ children, href, locale, ...props }: Record<string, unknown> & { children: React.ReactNode }) => (
    <a href={`${locale === "fr" ? "" : `/${String(locale)}`}${String(href)}`} {...props}>
      {children}
    </a>
  ),
}));

describe("LocaleSwitcher", () => {
  it("propose les deux langues sur la page courante et signale la langue active", () => {
    render(
      <NextIntlClientProvider locale="fr" messages={messages}>
        <LocaleSwitcher />
      </NextIntlClientProvider>,
    );
    expect(screen.getByRole("navigation", { name: "Langue" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "fr" })).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("link", { name: "en" })).toHaveAttribute("href", "/en/destinations");
  });
});
