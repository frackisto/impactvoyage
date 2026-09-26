import { Breadcrumbs, type Crumb } from "./breadcrumbs";
import { Container } from "./container";

type PageHeaderProps = {
  title: string;
  description?: string;
  breadcrumbs?: Crumb[];
};

/** Bandeau de titre des pages intérieures, avec fil d'Ariane. */
export function PageHeader({ title, description, breadcrumbs = [] }: PageHeaderProps) {
  return (
    <section className="bg-gradient-to-br from-ocean-800 to-ocean-950 text-white">
      <Container className="flex flex-col gap-3 py-10 sm:py-14">
        <Breadcrumbs items={breadcrumbs} />
        <h1 className="text-balance text-3xl font-bold sm:text-5xl">{title}</h1>
        {description && <p className="max-w-3xl text-lg text-ocean-100">{description}</p>}
      </Container>
    </section>
  );
}
