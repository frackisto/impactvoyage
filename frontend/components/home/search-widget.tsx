"use client";

import { BusFrontIcon, HotelIcon, MapIcon, SearchIcon, StampIcon, TicketIcon, type LucideIcon } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useId, type FormEvent, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useRouter } from "@/i18n/navigation";
import { countryName } from "@/lib/countries";
import { cn } from "@/lib/utils";

export type SearchOptions = {
  destinations: { slug: string; name: string }[];
  themes: { slug: string; name: string }[];
  visaCountries: { code: string; slug: string }[];
};

const PURPOSES = ["TOURISME", "AFFAIRES", "ETUDES", "FAMILLE", "TRANSIT"] as const;
const TRANSPORTS = ["TRANSFERT_AEROPORT", "BUS", "NAVETTE", "FERRY", "TRAIN", "CHAUFFEUR"] as const;
const DURATIONS = [3, 5, 7, 10, 15];

const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 md:text-sm";

function FormField({ label, children }: { label: string; children: (id: string) => ReactNode }) {
  const id = useId();
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-ocean-900">
        {label}
      </label>
      {children(id)}
    </div>
  );
}

/** Formulaire en grille avec bouton aligné ; les champs vides ne sont pas transmis. */
function SearchForm({ onSearch, children }: { onSearch: (params: URLSearchParams) => void; children: ReactNode }) {
  const t = useTranslations("Search");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    new FormData(event.currentTarget).forEach((value, key) => {
      if (typeof value === "string" && value.trim()) params.set(key, value.trim());
    });
    onSearch(params);
  }
  return (
    <form onSubmit={submit} className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-[repeat(auto-fit,minmax(10rem,1fr))]">
      {children}
      <Button type="submit" variant="cta" size="lg" className="w-full">
        <SearchIcon aria-hidden="true" data-icon="inline-start" />
        {t("submit")}
      </Button>
    </form>
  );
}

const today = () => new Date().toISOString().slice(0, 10);

/**
 * Moteur de recherche multifonction (CdC § 6, § 7) : un formulaire par onglet.
 * Les noms des champs sont ceux des filtres de l'API, que les pages de
 * résultats transmettent tels quels.
 */
export function SearchWidget({ options }: { options: SearchOptions }) {
  const t = useTranslations("Search");
  const locale = useLocale();
  const router = useRouter();
  const go = (path: string) => (params: URLSearchParams) => {
    const query = params.toString();
    router.push(query ? `${path}?${query}` : path);
  };

  const tabs: { value: string; icon: LucideIcon }[] = [
    { value: "tours", icon: MapIcon },
    { value: "hotels", icon: HotelIcon },
    { value: "visa", icon: StampIcon },
    { value: "activities", icon: TicketIcon },
    { value: "transport", icon: BusFrontIcon },
  ];

  const destinationSelect = (id: string) => (
    <select id={id} name="destination" className={selectClass} defaultValue="">
      <option value="">{t("anyDestination")}</option>
      {options.destinations.map((d) => (
        <option key={d.slug} value={d.slug}>
          {d.name}
        </option>
      ))}
    </select>
  );

  return (
    <div className="rounded-3xl border bg-background p-4 shadow-2xl shadow-ocean-950/20 sm:p-6">
      <h2 className="sr-only">{t("label")}</h2>
      <Tabs defaultValue="tours">
        <TabsList className="mb-5 flex h-auto w-full flex-wrap justify-start gap-1 bg-ocean-50 p-1">
          {tabs.map(({ value, icon: Icon }) => (
            <TabsTrigger
              key={value}
              value={value}
              className={cn(
                "h-10 flex-none gap-2 px-3 text-sm font-semibold sm:px-4",
                "data-active:bg-ocean-600 data-active:text-white",
              )}
            >
              <Icon aria-hidden="true" className="size-4" />
              {t(value)}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="tours">
          <SearchForm
            onSearch={(params) => {
              const scope = params.get("scope") === "INTERNATIONAL" ? "internationaux" : "nationaux";
              params.delete("scope");
              go(`/circuits/${scope}`)(params);
            }}
          >
            <FormField label={t("scope")}>
              {(id) => (
                <select id={id} name="scope" className={selectClass} defaultValue="NATIONAL">
                  <option value="NATIONAL">{t("national")}</option>
                  <option value="INTERNATIONAL">{t("international")}</option>
                </select>
              )}
            </FormField>
            <FormField label={t("destination")}>{destinationSelect}</FormField>
            <FormField label={t("departure")}>
              {(id) => <Input id={id} name="departure_from" type="date" min={today()} />}
            </FormField>
            <FormField label={t("duration")}>
              {(id) => (
                <select id={id} name="max_days" className={selectClass} defaultValue="">
                  <option value="">{t("anyDuration")}</option>
                  {DURATIONS.map((days) => (
                    <option key={days} value={days}>
                      {t("days", { count: days })}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
            <FormField label={t("theme")}>
              {(id) => (
                <select id={id} name="theme" className={selectClass} defaultValue="">
                  <option value="">{t("anyTheme")}</option>
                  {options.themes.map((theme) => (
                    <option key={theme.slug} value={theme.slug}>
                      {theme.name}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
            <FormField label={t("travelers")}>
              {(id) => <Input id={id} name="travelers" type="number" min={1} max={99} inputMode="numeric" />}
            </FormField>
            <FormField label={t("budget")}>
              {(id) => <Input id={id} name="max_price" type="number" min={0} step={5000} inputMode="numeric" />}
            </FormField>
          </SearchForm>
        </TabsContent>

        <TabsContent value="hotels">
          <SearchForm onSearch={go("/hotels")}>
            <FormField label={t("destination")}>{destinationSelect}</FormField>
            <FormField label={t("arrival")}>
              {(id) => <Input id={id} name="available_from" type="date" min={today()} />}
            </FormField>
            <FormField label={t("checkout")}>
              {(id) => <Input id={id} name="available_to" type="date" min={today()} />}
            </FormField>
            <FormField label={t("travelers")}>
              {(id) => <Input id={id} name="travelers" type="number" min={1} max={20} inputMode="numeric" />}
            </FormField>
            <FormField label={t("rooms")}>
              {(id) => <Input id={id} name="rooms" type="number" min={1} max={10} inputMode="numeric" />}
            </FormField>
            <FormField label={t("category")}>
              {(id) => (
                <select id={id} name="stars" className={selectClass} defaultValue="">
                  <option value="">{t("anyCategory")}</option>
                  {[3, 4, 5].map((stars) => (
                    <option key={stars} value={stars}>
                      {t("stars", { count: stars })}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
            <FormField label={t("budget")}>
              {(id) => <Input id={id} name="max_price" type="number" min={0} step={5000} inputMode="numeric" />}
            </FormField>
          </SearchForm>
        </TabsContent>

        <TabsContent value="visa">
          <SearchForm
            onSearch={(params) => {
              // Pays connu : page dédiée (/visa/france) ; sinon, recherche filtrée.
              const country = options.visaCountries.find(
                (c) => c.code === params.get("destination_country_code"),
              );
              if (country && !params.get("purpose")) return go(`/visa/${country.slug}`)(new URLSearchParams());
              go("/visa")(params);
            }}
          >
            <FormField label={t("country")}>
              {(id) => (
                <select id={id} name="destination_country_code" className={selectClass} defaultValue="">
                  <option value="">{t("anyCountry")}</option>
                  {options.visaCountries.map((c) => (
                    <option key={c.code} value={c.code}>
                      {countryName(c.code, locale)}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
            <FormField label={t("purpose")}>
              {(id) => (
                <select id={id} name="purpose" className={selectClass} defaultValue="">
                  <option value="">{t("anyPurpose")}</option>
                  {PURPOSES.map((purpose) => (
                    <option key={purpose} value={purpose}>
                      {t(`purpose${purpose}`)}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
          </SearchForm>
        </TabsContent>

        <TabsContent value="activities">
          <SearchForm onSearch={go("/activites")}>
            <FormField label={t("destination")}>{destinationSelect}</FormField>
            <FormField label={t("date")}>
              {(id) => <Input id={id} name="date" type="date" min={today()} />}
            </FormField>
            <FormField label={t("budget")}>
              {(id) => <Input id={id} name="max_price" type="number" min={0} step={5000} inputMode="numeric" />}
            </FormField>
          </SearchForm>
        </TabsContent>

        <TabsContent value="transport">
          <SearchForm onSearch={go("/transport")}>
            <FormField label={t("transportType")}>
              {(id) => (
                <select id={id} name="transport_type" className={selectClass} defaultValue="">
                  <option value="">{t("anyTransport")}</option>
                  {TRANSPORTS.map((type) => (
                    <option key={type} value={type}>
                      {t(`transport${type}`)}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
            <FormField label={t("origin")}>
              {(id) => <Input id={id} name="origin" placeholder={t("originPlaceholder")} autoComplete="off" />}
            </FormField>
            <FormField label={t("to")}>
              {(id) => <Input id={id} name="destination" placeholder={t("toPlaceholder")} autoComplete="off" />}
            </FormField>
            <FormField label={t("date")}>
              {(id) => <Input id={id} name="date" type="date" min={today()} />}
            </FormField>
            <FormField label={t("travelers")}>
              {(id) => <Input id={id} name="passengers" type="number" min={1} max={99} inputMode="numeric" />}
            </FormField>
          </SearchForm>
        </TabsContent>
      </Tabs>
    </div>
  );
}
