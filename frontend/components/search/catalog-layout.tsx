type CatalogLayoutProps = {
  /** Panneau de filtres (colonne de gauche sur grand écran). */
  filters: React.ReactNode;
  /** Nombre de résultats, annoncé comme titre de la zone de résultats. */
  heading: string;
  sort?: React.ReactNode;
  /** Résultats, pagination ou état vide. */
  children: React.ReactNode;
};

/** Mise en page des listes filtrables (circuits, hébergements...). */
export function CatalogLayout({ filters, heading, sort, children }: CatalogLayoutProps) {
  return (
    <div className="grid gap-8 lg:grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="lg:sticky lg:top-24 lg:self-start">{filters}</aside>
      <section aria-labelledby="catalog-results" className="flex flex-col gap-6">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <h2 id="catalog-results" className="text-lg font-semibold text-ocean-900">
            {heading}
          </h2>
          {sort}
        </div>
        {children}
      </section>
    </div>
  );
}

/** Grille de cartes de résultats. */
export function ResultGrid({ children }: { children: React.ReactNode }) {
  return <ul className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">{children}</ul>;
}
