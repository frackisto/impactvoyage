import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import messages from "@/messages/fr.json";

import { Pagination } from "./pagination";

vi.mock("@/i18n/navigation", () => ({
  Link: ({ children, href, ...props }: Record<string, unknown> & { children: React.ReactNode }) => (
    <a href={String(href)} {...props}>
      {children}
    </a>
  ),
}));

function renderPagination(props: Partial<React.ComponentProps<typeof Pagination>> = {}) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      <Pagination page={5} count={120} pageSize={12} pathname="/hotels" query={{ stars: "4" }} {...props} />
    </NextIntlClientProvider>,
  );
}

describe("Pagination", () => {
  it("rien à afficher quand tout tient sur une page", () => {
    const { container } = renderPagination({ page: 1, count: 12 });
    expect(container).toBeEmptyDOMElement();
  });

  it("page courante signalée, voisines, extrémités et filtres conservés", () => {
    renderPagination();
    expect(screen.getByRole("navigation", { name: "Pagination" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Page 5" })).toHaveAttribute("aria-current", "page");
    const pages = screen.getAllByRole("link", { name: /^Page \d+$/ }).map((link) => link.textContent);
    expect(pages).toEqual(["1", "4", "5", "6", "10"]);
    expect(screen.getByRole("link", { name: "Page 1" })).toHaveAttribute("href", "/hotels?stars=4");
    expect(screen.getByRole("link", { name: "Page suivante" })).toHaveAttribute("href", "/hotels?stars=4&page=6");
    expect(screen.getByRole("link", { name: "Page précédente" })).toHaveAttribute("rel", "prev");
  });

  it("pas de lien « précédente » sur la première page ni « suivante » sur la dernière", () => {
    const { unmount } = renderPagination({ page: 1 });
    expect(screen.queryByRole("link", { name: "Page précédente" })).toBeNull();
    unmount();
    renderPagination({ page: 10 });
    expect(screen.queryByRole("link", { name: "Page suivante" })).toBeNull();
  });
});
