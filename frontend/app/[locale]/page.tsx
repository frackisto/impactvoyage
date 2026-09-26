import { setRequestLocale } from "next-intl/server";

import { Hero } from "@/components/home/hero";
import { SearchWidget } from "@/components/home/search-widget";
import {
  AboutSection,
  ContactBand,
  DestinationsSection,
  EventsSection,
  OffersSection,
  ResidencesSection,
  ReviewsSection,
  ServicesSection,
  ToursSection,
  VisaSection,
  WhyUsSection,
} from "@/components/home/sections";
import { getHomeData } from "@/services/home.service";
import { getSiteSettings } from "@/services/site.service";

/**
 * Accueil (CdC § 6) : hero et moteur de recherche multifonction, puis les
 * contenus gérés dans l'admin. Une section sans contenu (ex. aucun circuit
 * publié) n'est pas affichée.
 */
export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [settings, data] = await Promise.all([getSiteSettings(), getHomeData()]);

  const searchOptions = {
    destinations: data.allDestinations.map(({ slug, name }) => ({ slug, name })),
    themes: data.themes.map(({ slug, name }) => ({ slug, name })),
    visaCountries: [
      ...new Map(
        data.visas.map((v) => [v.destination_country_code, { code: v.destination_country_code, slug: v.country_slug }]),
      ).values(),
    ],
  };

  return (
    <>
      <Hero settings={settings}>
        <SearchWidget options={searchOptions} />
      </Hero>
      <ServicesSection services={data.services} />
      <DestinationsSection destinations={data.destinations} />
      <ToursSection tours={data.tours} />
      <OffersSection offers={data.offers} />
      <VisaSection visas={data.visas} services={data.services} />
      <AboutSection />
      <WhyUsSection />
      <ResidencesSection residences={data.residences} />
      <EventsSection events={data.events} />
      <ReviewsSection reviews={data.reviews} />
      <ContactBand settings={settings} />
    </>
  );
}
