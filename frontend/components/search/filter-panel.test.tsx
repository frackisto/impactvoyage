import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FilterPanel, type FilterField } from "./filter-panel";

const push = vi.fn();

vi.mock("@/i18n/navigation", () => ({
  useRouter: () => ({ push }),
  // « scroll » est une option de navigation de Next.js, pas un attribut HTML.
  Link: ({ children, href, ...props }: Record<string, unknown> & { children: React.ReactNode }) => (
    <a href={String(href)} {...Object.fromEntries(Object.entries(props).filter(([key]) => key !== "scroll"))}>
      {children}
    </a>
  ),
}));

const FIELDS: FilterField[] = [
  {
    type: "select",
    name: "destination",
    label: "Destination",
    anyLabel: "Toutes",
    options: [
      { value: "dubai", label: "Dubaï" },
      { value: "abidjan", label: "Abidjan" },
    ],
  },
  { type: "select", name: "theme", label: "Thème", anyLabel: "Tous", options: [] },
  { type: "text", name: "search", label: "Mot-clé" },
  {
    type: "checkboxes",
    name: "amenities",
    label: "Équipements",
    options: [
      { value: "1", label: "Wi-Fi" },
      { value: "4", label: "Piscine" },
    ],
  },
];

const LABELS = { title: "Filtres", formLabel: "Filtrer les hôtels", apply: "Appliquer", reset: "Effacer" };

function renderPanel(current: Record<string, string | undefined> = {}) {
  return render(
    <FilterPanel pathname="/hotels" fields={FIELDS} current={current} keep={{ ordering: "price" }} labels={LABELS} />,
  );
}

describe("FilterPanel", () => {
  beforeEach(() => push.mockClear());

  it("une liste déroulante s'applique aussitôt, en gardant le tri et en revenant en page 1", async () => {
    renderPanel({ page: "3" });
    await userEvent.selectOptions(screen.getByLabelText("Destination"), "dubai");
    expect(push).toHaveBeenCalledWith("/hotels?ordering=price&destination=dubai", { scroll: false });
  });

  it("les cases cochées sont jointes par des virgules", async () => {
    renderPanel({ amenities: "4" });
    expect(screen.getByLabelText("Piscine")).toBeChecked();
    await userEvent.click(screen.getByLabelText("Wi-Fi"));
    expect(push).toHaveBeenLastCalledWith("/hotels?ordering=price&amenities=1%2C4", { scroll: false });
  });

  it("un champ libre s'applique avec le bouton, espaces retirés", async () => {
    renderPanel();
    await userEvent.type(screen.getByLabelText("Mot-clé"), "  lagune ");
    expect(push).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Appliquer" }));
    expect(push).toHaveBeenCalledWith("/hotels?ordering=price&search=lagune", { scroll: false });
  });

  it("filtres sans option masqués ; « Effacer » seulement quand un filtre est actif", () => {
    const { unmount } = renderPanel();
    expect(screen.queryByLabelText("Thème")).toBeNull();
    expect(screen.queryByRole("link", { name: "Effacer" })).toBeNull();
    unmount();
    renderPanel({ destination: "abidjan" });
    expect(screen.getByRole("link", { name: "Effacer" })).toHaveAttribute("href", "/hotels?ordering=price");
    expect(screen.getByRole("button", { name: /Filtres/ })).toHaveTextContent("1");
  });
});
