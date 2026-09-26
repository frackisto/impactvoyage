import type { Money } from "@/types";

const INTL_LOCALE: Record<string, string> = { fr: "fr-FR", en: "en-GB" };

export function intlLocale(locale: string): string {
  return INTL_LOCALE[locale] ?? locale;
}

/** 150000 XOF → « 150 000 F CFA » (fr) ; 228.67 EUR → « 228,67 € ». */
export function formatAmount(amount: string | number, currency: string, locale: string): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  return new Intl.NumberFormat(intlLocale(locale), {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "XOF" ? 0 : 2,
  }).format(value);
}

/**
 * Prix à afficher : la conversion dans la devise choisie par le visiteur si
 * elle existe (montant indicatif), sinon le prix d'origine.
 */
export function displayMoney(money: Money, locale: string) {
  const main = money.display ?? { amount: money.amount, currency: money.currency };
  return {
    text: formatAmount(main.amount, main.currency, locale),
    original: money.display ? formatAmount(money.amount, money.currency, locale) : null,
    isConverted: Boolean(money.display),
  };
}

/** 4.5 → « 4,5 » (fr). */
export function formatRating(value: number, locale: string): string {
  return new Intl.NumberFormat(intlLocale(locale), { maximumFractionDigits: 1 }).format(value);
}

export function formatDate(value: string | Date, locale: string, options?: Intl.DateTimeFormatOptions) {
  const date = typeof value === "string" ? new Date(value) : value;
  return new Intl.DateTimeFormat(intlLocale(locale), options ?? { dateStyle: "long" }).format(date);
}

/** Montant multiplié (ex. prix par nuit × nuits × chambres), conversion d'affichage comprise. */
export function multiplyMoney(money: Money, factor: number): Money {
  const times = (amount: string) => (Number(amount) * factor).toFixed(2);
  return {
    ...money,
    amount: times(money.amount),
    display: money.display ? { ...money.display, amount: times(money.display.amount) } : money.display,
  };
}

/** Durée en heures : « 1,5 h » (fr), « 1.5 hr » (en). */
export function formatHours(value: string | number, locale: string): string {
  return new Intl.NumberFormat(intlLocale(locale), { style: "unit", unit: "hour", unitDisplay: "short", maximumFractionDigits: 1 }).format(
    Number(value),
  );
}
