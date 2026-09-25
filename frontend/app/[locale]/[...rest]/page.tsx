import { notFound } from "next/navigation";

/** Toute URL inconnue d'une langue affiche la page 404 traduite. */
export default function CatchAll() {
  notFound();
}
