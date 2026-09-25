import { CalendarDaysIcon, ClockIcon, UsersIcon } from "lucide-react";
import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";

import { Container } from "@/components/common/container";
import { ContentCard } from "@/components/common/content-card";
import { OfferBadge } from "@/components/common/offer-badge";
import { PageHeader } from "@/components/common/page-header";
import { Price } from "@/components/common/price";
import { Rating } from "@/components/common/rating";
import { SectionHeading } from "@/components/common/section-heading";
import { CardGridSkeleton, EmptyState, ErrorState } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { DemoForm } from "./demo-form";

export const metadata: Metadata = {
  title: "Charte graphique",
  robots: { index: false, follow: false },
};

const PALETTES = {
  ocean: ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950"],
  sunset: ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900", "950"],
};

// Classes écrites en toutes lettres : Tailwind ne génère que les classes présentes dans le code.
const SWATCH: Record<string, string> = {
  "ocean-50": "bg-ocean-50", "ocean-100": "bg-ocean-100", "ocean-200": "bg-ocean-200",
  "ocean-300": "bg-ocean-300", "ocean-400": "bg-ocean-400", "ocean-500": "bg-ocean-500",
  "ocean-600": "bg-ocean-600", "ocean-700": "bg-ocean-700", "ocean-800": "bg-ocean-800",
  "ocean-900": "bg-ocean-900", "ocean-950": "bg-ocean-950",
  "sunset-50": "bg-sunset-50", "sunset-100": "bg-sunset-100", "sunset-200": "bg-sunset-200",
  "sunset-300": "bg-sunset-300", "sunset-400": "bg-sunset-400", "sunset-500": "bg-sunset-500",
  "sunset-600": "bg-sunset-600", "sunset-700": "bg-sunset-700", "sunset-800": "bg-sunset-800",
  "sunset-900": "bg-sunset-900", "sunset-950": "bg-sunset-950",
};

const DEMO_PRICE = { amount: "450000.00", currency: "XOF" };
const DEMO_PRICE_EUR = { ...DEMO_PRICE, display: { amount: "686.02", currency: "EUR" } };

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-6 border-b py-12 last:border-0">
      <h2 className="text-2xl font-bold text-ocean-900">{title}</h2>
      {children}
    </section>
  );
}

/** Référence visuelle du design system (page interne, non indexée). */
export default async function StyleGuidePage({ params }: PageProps<"/[locale]/charte-graphique">) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <>
      <PageHeader
        title="Charte graphique"
        description="Couleurs du logo, typographies et composants réutilisables du site."
        breadcrumbs={[{ label: "Charte graphique" }]}
      />
      <Container>
        <Section title="Couleurs">
          {Object.entries(PALETTES).map(([name, steps]) => (
            <div key={name} className="flex flex-col gap-2">
              <p className="font-semibold">
                {name === "ocean" ? "Ocean — bleu du logo (#1F8FC4 = 500)" : "Sunset — orange du logo (#F89832 = 500)"}
              </p>
              <div className="grid grid-cols-6 gap-2 sm:grid-cols-11">
                {steps.map((step) => (
                  <div key={step} className="flex flex-col gap-1 text-xs">
                    <div className={`h-14 rounded-lg border ${SWATCH[`${name}-${step}`]}`} />
                    <span className={step === "500" ? "font-bold" : undefined}>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <p className="text-sm text-muted-foreground">
            Texte blanc à partir de <strong>ocean-600</strong> (contraste 4,7:1) ; sur l&apos;orange,
            texte <strong>ocean-950</strong> (7,2:1), jamais de blanc.
          </p>
        </Section>

        <Section title="Typographies">
          <div className="flex flex-col gap-3">
            <p className="font-heading text-5xl font-bold text-ocean-800">Fredoka — titres</p>
            <p className="text-lg">Nunito — texte courant, lisible sur tous les écrans. Àâçéèêëîïôûùüÿ.</p>
            <p className="font-script text-4xl text-sunset-600">Voyagez, Rêvez, Explorez.</p>
          </div>
          <SectionHeading
            eyebrow="Sur-titre"
            title="Titre de section"
            description="Paragraphe d'introduction d'une section de page."
          />
        </Section>

        <Section title="Boutons">
          <div className="flex flex-wrap items-center gap-3">
            <Button>Principal</Button>
            <Button variant="cta">Demander un devis</Button>
            <Button variant="outline">Secondaire</Button>
            <Button variant="secondary">Tertiaire</Button>
            <Button variant="ghost">Discret</Button>
            <Button variant="link">Lien</Button>
            <Button disabled>Désactivé</Button>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button size="sm">Petit</Button>
            <Button>Normal (40 px)</Button>
            <Button size="lg">Grand (44 px)</Button>
          </div>
          <div className="flex flex-wrap gap-3 rounded-2xl bg-ocean-900 p-6">
            <Button variant="inverse" size="lg">Sur fond sombre</Button>
            <Button variant="cta" size="lg">Demander un devis</Button>
          </div>
        </Section>

        <Section title="Badges, prix et notes">
          <div className="flex flex-wrap gap-2">
            <OfferBadge code="NOUVEAU" />
            <OfferBadge code="PROMOTION" />
            <OfferBadge code="POPULAIRE" />
            <OfferBadge code="DERNIERES_PLACES" />
            <Badge variant="secondary">Circuit national</Badge>
            <Badge variant="outline">7 jours</Badge>
          </div>
          <div className="flex flex-wrap items-end gap-8">
            <Price value={DEMO_PRICE} from unit="person" />
            <Price value={DEMO_PRICE_EUR} from unit="person" />
            <div className="flex flex-col">
              <Price value={{ amount: "600000.00", currency: "XOF" }} strikethrough />
              <Price value={DEMO_PRICE} />
            </div>
            <Rating value={4.6} count={128} />
          </div>
        </Section>

        <Section title="Cartes de contenu">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <ContentCard
              href="/charte-graphique"
              title="Découverte d'Assinie et de Grand-Bassam"
              eyebrow="Côte d'Ivoire · Circuit national"
              description="Plages, patrimoine colonial classé à l'UNESCO et lagune : trois jours pour découvrir le littoral ivoirien."
              badges={<OfferBadge code="POPULAIRE" />}
              meta={
                <>
                  <span className="inline-flex items-center gap-1"><ClockIcon aria-hidden="true" className="size-4" /> 3 jours</span>
                  <Rating value={4.8} count={42} />
                </>
              }
              footer={<Price value={DEMO_PRICE} from unit="person" />}
            />
            <ContentCard
              href="/charte-graphique"
              title="Dubaï, entre désert et gratte-ciel"
              eyebrow="Émirats arabes unis · International"
              description="Safari dans le désert, croisière sur la marina et visite de Burj Khalifa."
              badges={<OfferBadge code="DERNIERES_PLACES" />}
              meta={
                <>
                  <span className="inline-flex items-center gap-1"><CalendarDaysIcon aria-hidden="true" className="size-4" /> 12 nov.</span>
                  <span className="inline-flex items-center gap-1"><UsersIcon aria-hidden="true" className="size-4" /> 3 places</span>
                </>
              }
              footer={<Price value={DEMO_PRICE_EUR} from unit="person" />}
            />
            <ContentCard
              href="/charte-graphique"
              title="Carte sans image"
              eyebrow="Illustration de repli"
              description="Quand une photo manque, un pictogramme la remplace sans casser la mise en page."
            />
          </div>
        </Section>

        <Section title="Onglets (moteur de recherche)">
          <Tabs defaultValue="tours" className="max-w-xl">
            <TabsList>
              <TabsTrigger value="tours">Tours</TabsTrigger>
              <TabsTrigger value="hotels">Hôtels</TabsTrigger>
              <TabsTrigger value="visa">Visa</TabsTrigger>
            </TabsList>
            <TabsContent value="tours" className="pt-3 text-muted-foreground">Formulaire de recherche de circuits.</TabsContent>
            <TabsContent value="hotels" className="pt-3 text-muted-foreground">Formulaire de recherche d&apos;hôtels.</TabsContent>
            <TabsContent value="visa" className="pt-3 text-muted-foreground">Formulaire de recherche de visas.</TabsContent>
          </Tabs>
        </Section>

        <Section title="Formulaire">
          <DemoForm />
        </Section>

        <Section title="États : vide, erreur, chargement">
          <div className="grid gap-6 lg:grid-cols-2">
            <EmptyState
              title="Aucun circuit ne correspond"
              description="Essayez d'élargir vos dates ou votre budget."
              action={<Button variant="outline">Réinitialiser les filtres</Button>}
            />
            <ErrorState
              title="Impossible de charger les circuits"
              description="Vérifiez votre connexion puis réessayez."
              action={<Button>Réessayer</Button>}
            />
          </div>
          <CardGridSkeleton count={3} label="Chargement…" />
        </Section>
      </Container>
    </>
  );
}
